#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import os
import time
from kubernetes import client
import logging
import traceback
from functools import wraps

from .container_manager import ContainerManager, InvalidServiceRequestError, ContainerService

RETRY_WAIT_SECS = 1
RETRY_TIMES = 5

logger = logging.getLogger(__name__)


class ServiceRequestError(Exception):
    pass


class KubernetesContainerManager(ContainerManager):

    def __init__(self, **kwargs):
        aToken = None
        with open('/var/run/secrets/kubernetes.io/serviceaccount/token',
                  'r') as fToken:
            aToken = fToken.read()

        # Create a configuration object
        aConfiguration = client.Configuration()

        # Specify the endpoint of your Kube cluster
        aConfiguration.host = "https://{}:{}".format(
            os.getenv('KUBERNETES_SERVICE_HOST'),
            os.getenv('KUBERNETES_SERVICE_PORT'))

        # Security part.
        # In this simple example we are not going to verify the SSL certificate of
        # the remote cluster (for simplicity reason)
        aConfiguration.verify_ssl = False
        # Nevertheless if you want to do it you can with these 2 parameters
        # configuration.verify_ssl=True
        # ssl_ca_cert is the filepath to the file that contains the certificate.
        # configuration.ssl_ca_cert="certificate"

        aConfiguration.api_key = {"authorization": "Bearer " + aToken}

        # Create a ApiClient with our config
        aApiClient = client.ApiClient(aConfiguration)

        self._client_deployment = client.AppsV1Api(aApiClient)
        self._client_service = client.CoreV1Api(aApiClient)
        self.api_instance = client.NetworkingV1beta1Api(aApiClient)

    def update_ingress(self, ingress_name: str, ingress_body: dict):
        paths = self._update_ingress_paths(ingress_body)
        body = client.NetworkingV1beta1Ingress(
            api_version="networking.k8s.io/v1beta1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                                                    name=ingress_name,
                                                    annotations={
                                                        "nginx.ingress.kubernetes.io/rewrite-target": "/"
                                                        }
                                                    ),
            spec=client.NetworkingV1beta1IngressSpec(
                rules=[client.NetworkingV1beta1IngressRule(
                    http=client.NetworkingV1beta1HTTPIngressRuleValue(
                        paths=paths
                    )
                )
                ]
            )
        )

        # check the current ingress list
        ingress_list = self.api_instance.list_namespaced_ingress_with_http_info(namespace='default')

        if ingress_list[1] != 200:
            raise ServiceRequestError("ingress response code is not 200")

        # get the ingress name of each ingress
        ingress_names = [ele.metadata.name for ele in ingress_list[0].items]

        # check if the ingress_name in the list
        if ingress_name in ingress_names:

            # if the ingress is exist, update it
            self.api_instance.replace_namespaced_ingress_with_http_info(name=ingress_name,
                                                                        namespace='default',
                                                                        body=body)
        else:
            # otherwise, create new one
            self.api_instance.create_namespaced_ingress_with_http_info(namespace='default',
                                                                       body=body)

    def _update_ingress_paths(self, ingress_body: dict) -> list:
        paths = list()
        for path_info in ingress_body["spec"]["rules"][0]["http"]["paths"]:
            path_obj = client.NetworkingV1beta1HTTPIngressPath(
                            path=path_info["path"],
                            backend=client.NetworkingV1beta1IngressBackend(
                                service_port=path_info["backend"]["servicePort"],
                                service_name=path_info["backend"]["serviceName"])

                        )
            paths.append(path_obj)

        return paths

    def destroy_service(self, service: ContainerService):
        self._client_deployment.delete_namespaced_deployment(service.id, namespace='default')
        self._client_service.delete_namespaced_service(service.id, namespace='default')

    def create_service(self,
                       service_name,
                       docker_image,
                       replicas,
                       args,
                       environment_vars,
                       mounts={},
                       publish_port=None,
                       gpus=0) -> ContainerService:
        hostname = service_name
        if publish_port is not None:
            service_config = self._create_service_config(service_name, docker_image, replicas,
                            args, environment_vars, mounts, publish_port,
                            gpus)
            service_obj = _retry(self._client_service.create_namespaced_service)(namespace='default', body=service_config)
        deployment_config = self._create_deployment_config(service_name, docker_image, replicas,
                        args, environment_vars, mounts, publish_port,
                        gpus)
        deployment_obj = _retry(self._client_deployment.create_namespaced_deployment)(namespace='default',
                                                                                      body=deployment_config)

        info = {
            'node_id': 'default',
            'gpu_nos': gpus,
            'service_name': service_name,
            'replicas': replicas
        }

        service = ContainerService(
            service_name, hostname,
            publish_port[0] if publish_port is not None else None, info)
        return service

    def _create_deployment_config(self,
                                  service_name,
                                  docker_image,
                                  replicas,
                                  args,
                                  environment_vars,
                                  mounts={},
                                  publish_port=None,
                                  gpus=0):
        content = {}
        content.setdefault('apiVersion', 'apps/v1')
        content.setdefault('kind', 'Deployment')
        metadata = content.setdefault('metadata', {})
        metadata.setdefault('name', service_name)
        labels = metadata.setdefault('labels', {})
        labels.setdefault('name', service_name)
        spec = content.setdefault('spec', {})
        spec.setdefault('replicas', replicas)
        spec.setdefault('selector', {'matchLabels': {'name': service_name}})
        template = spec.setdefault('template', {})
        template.setdefault('metadata', {'labels': {'name': service_name}})
        container = {}
        container.setdefault('name', service_name)
        container.setdefault('image', docker_image)
        volumeMounts = container.setdefault('volumeMounts', [])
        volumes = []
        mounts_count = 0
        for (k, v) in mounts.items():
            volumeMounts.append({
                'name': 'v' + str(mounts_count),
                'mountPath': v
            })
            volumes.append({
                'name': 'v' + str(mounts_count),
                'hostPath': {
                    'path': k
                }
            })
            mounts_count += 1
        template.setdefault('spec', {
            'containers': [container],
            'volumes': volumes
        })
        env = [{'name': k, 'value': v} for (k, v) in environment_vars.items()]
        container.setdefault('env', env)
        if gpus > 0:
            container.setdefault('resources',
                                 {'limits': {
                                     'nvidia.com/gpu': gpus
                                 }})
        return content

    def _create_service_config(self,
                               service_name,
                               docker_image,
                               replicas,
                               args,
                               environment_vars,
                               mounts={},
                               publish_port=None,
                               gpus=0):
        #admin service
        content = {}
        content.setdefault('apiVersion', 'v1')
        content.setdefault('kind', 'Service')
        metadata = content.setdefault('metadata', {})
        metadata.setdefault('name', service_name)
        labels = metadata.setdefault('labels', {})
        labels.setdefault('name', service_name)
        spec = content.setdefault('spec', {})
        if publish_port is not None:
            spec.setdefault('type', 'NodePort')
            ports = spec.setdefault('ports', [])
            ports.append({
                'port': int(publish_port[1]),
                'targetPort': int(publish_port[1]),
                'nodePort': int(publish_port[0])
            })
        spec.setdefault('selector', {'name': service_name})
        return content


# Decorator that retries a method call a number of times
def _retry(func):
    wait_secs = RETRY_WAIT_SECS

    @wraps(func)
    def retried_func(*args, **kwargs):
        for no in range(RETRY_TIMES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f'Error when calling `{func}`:')
                logger.error(traceback.format_exc())

                # Retried so many times but still errors - raise exception
                if no == RETRY_TIMES:
                    raise e

            logger.info(f'Retrying {func} after {wait_secs}s...')
            time.sleep(wait_secs)

    return retried_func
