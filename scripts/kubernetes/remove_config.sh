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

rm -f ./scripts/kubernetes/start_admin_deployment.json
rm -f ./scripts/kubernetes/start_redis_deployment.json
rm -f ./scripts/kubernetes/start_web_admin_deployment.json
rm -f ./scripts/kubernetes/start_db_deployment.json
rm -f ./scripts/kubernetes/start_zookeeper_deployment.json
rm -f ./scripts/kubernetes/start_kafka_deployment.json
rm -f ./scripts/kubernetes/start_kibana_deployment.json
rm -f ./scripts/kubernetes/start_logstash_deployment.json
rm -f ./scripts/kubernetes/start_es_deployment.json

rm -f ./scripts/kubernetes/start_admin_service.json
rm -f ./scripts/kubernetes/start_redis_service.json
rm -f ./scripts/kubernetes/start_web_admin_service.json
rm -f ./scripts/kubernetes/start_db_service.json
rm -f ./scripts/kubernetes/start_zookeeper_service.json
rm -f ./scripts/kubernetes/start_kafka_service.json
rm -f ./scripts/kubernetes/start_kibana_service.json
rm -f ./scripts/kubernetes/start_logstash_service.json
rm -f ./scripts/kubernetes/start_es_service.json
rm -f ./scripts/kubernetes/spark-app.json
