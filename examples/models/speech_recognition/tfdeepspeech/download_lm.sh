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
LM_PATH=tfdeepspeech/lm.binary

# Download pre-built LM from https://github.com/mozilla/DeepSpeech/tree/v0.6.0-alpha.4/data/lm
mkdir -p tfdeepspeech/
curl https://media.githubusercontent.com/media/mozilla/DeepSpeech/v0.6.0-alpha.4/data/lm/lm.binary -o $LM_PATH
echo "LM downloaded to $LM_PATH"
