# Copyright 2015 Datawire. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import yaml

def name_version(namever):
    parts = namever.split() # split on whitespace
    if len(parts) not in [1, 2]:
        raise ValueError(namever)
    name = parts.pop(0)
    if parts:
        version = parts.pop(0)
    else:
        version = "1.0.0"
    return name, version

def load_yaml(path):
    # configure the yaml parser to allow grabbing OS environment variables in the config.
    # TODO(plombardi:) Improve so that the default argument is optional
    pattern = re.compile(r'^(.*)<%= ENV\[\'(.*)\',\'(.*)\'\] %>(.*)$')
    yaml.add_implicit_resolver('!env_regex', pattern)

    def env_regex(loader, doc_node):
        value = loader.construct_scalar(doc_node)
        front, variable_name, default, back = pattern.match(value).groups()
        return str(front) + os.getenv(variable_name, default) + str(back)

    yaml.add_constructor('!env_regex', env_regex)

    with open(path, 'r') as stream:
        return yaml.load(stream)
