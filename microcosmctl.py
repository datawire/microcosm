#!/usr/bin/env python

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

"""microcosmctl.py

Usage:
    microcosmctl.py <architecture-file>
    microcosmctl.py (-h | --help)
    microcosmctl.py --version

Options:
    -h --help           Show the help.
    --version           Show the version.
"""

import os
import re
import subprocess
import sys
import yaml
import logging

from docopt import docopt
from toposort import toposort, toposort_flatten

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger('microcosmctl.py')


def load_config(path):

    """Reads a Microcosm configuration file.

    :param path: the path to the configuration file
    :return: a dictionary containing configuration values
    """

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


def setup():
    if not os.path.exists(os.getcwd() + "/.microcosm"):
        os.mkdir(os.getcwd() + "/.microcosm")


def create_state_dir(architecture):
    arch_state_path = os.getcwd() + "/.microcosm/" + architecture

    if not os.path.exists(arch_state_path):
        os.mkdir(arch_state_path)

    if not os.path.exists(arch_state_path + "/logs"):
        os.mkdir(arch_state_path + "/logs")

    return arch_state_path


def run_controller(args):
    setup()

    architecture_file = args['<architecture-file>']
    architecture = load_config(architecture_file)
    if not architecture['services']:
        raise ValueError('No services defined')

    state_dir_path = create_state_dir(architecture['name'])

    services_definitions = architecture['services']
    deploy_graph = {}
    for service_name, service_definition in services_definitions.iteritems():
        deploy_graph[service_name] = set(service_definition.get('dependencies', {}))

    deploy_graph = list(toposort_flatten(deploy_graph))

    # Iterate over the deployment graph and start a microcosm process for each service described. This code is a little
    # clumsy right now because we're retrofitting microcosmctl.py to work with microcosm.py by using it's config file.
    port = 5000
    pid_map = {}
    pid_map_file = state_dir_path + '/pids.yml'
    for service_name in deploy_graph:
        service_config = {
            'service': str(service_name),
            'version': str(services_definitions[service_name].get('version', '1.0')),
            'dependencies': services_definitions[service_name].get('dependencies', []),
            'http_service': {
                'address': '127.0.0.1',
            }
        }

        service_config_file = state_dir_path + '/' + service_name + '.yml'
        with open(service_config_file, 'w+') as f:
            yaml.dump(service_config, f)

        count = services_definitions[service_name].get('count', 1)
        for i in range(count):
            logger.info("Starting service... (name: %s, port: %s)", service_name, port)
            log_file = open(state_dir_path + "/logs/" + service_name + "." + str(i) + ".log", "w+")
            proc = subprocess.Popen([sys.executable, 'microcosm.py', '--http-port=' + str(port), service_config_file],
                                    env=os.environ.copy(),
                                    shell=False,
                                    stdout=log_file,
                                    stderr=subprocess.STDOUT,
                                    preexec_fn=os.setpgrp,
                                    close_fds=True,
                                    universal_newlines=True)

            if service_name not in pid_map:
                pid_map[service_name] = [proc.pid]
            else:
                pid_map[service_name].append(proc.pid)

            port += 1

    with open(pid_map_file, 'w+') as f:
        yaml.dump(pid_map, f)

    exit()


def main():
    exit(run_controller(docopt(__doc__, version='microcosmctl.py 0.0.1')))


if __name__ == "__main__":
    main()
