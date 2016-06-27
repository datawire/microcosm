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
    microcosmctl.py create  <architecture-file>
    microcosmctl.py destroy <architecture-name>
    microcosmctl.py (-h | --help)
    microcosmctl.py --version

Options:
    -h --help           Show the help.
    --version           Show the version.
"""

"""microcosmctl.py

Usage:
    microcosmctl.py deploy <architecture-file>
    microcosmctl.py kill   <architecture>
    microcosmctl.py (-h | --help)
    microcosmctl.py --version

Options:
    -h --help           Show the help.
    --version           Show the version.
"""

import errno
import os
import re
import subprocess
import sys
import yaml
import json
import logging
import signal

from docopt import docopt
from toposort import toposort, toposort_flatten

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger('microcosmctl.py')


def load_architecture(path):

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


def setup_state_dir(arch_name):
    path = ".microcosm/{}".format(arch_name)
    try:
        logger.info("Initializing architecture state directory (path: %s)", path)
        os.makedirs(path)
        os.makedirs("{}/logs".format(path))
        if not os.path.exists("{}/state.json".format(path)):
            logger.info("Initializing empty state file...")
            with open("{}/state.json".format(path), 'w+') as f:
                f.write('{}')

    except OSError:
        if not os.path.isdir(path):
            raise

    return path


def update_state(arch_name, state):
    path = ".microcosm/{}/state.json".format(arch_name)
    with open(path, 'w+') as f:
        json.dump(state, f, indent=4)


def destroy(args, state):
    logger.info("Destroying architecture (name: %s)", args['<architecture-name>'])
    running_services = state['running_services']
    for name, infos in running_services.iteritems():
        for info in running_services[name]:
            logger.info("Terminating service instance (name: %s, slug: %s)", name, info['pid'])
            os.kill(int(info['pid']), signal.SIGKILL)

    state['running_services'] = {}
    update_state(args['<architecture-name>'], state)


def create(args, arch, arch_state, arch_state_dir):
    service_definitions = arch.get('services', {})
    if len(service_definitions) < 1:
        raise ValueError("""Architecture definition "{}" is missing "services" or has an empty "services" key. Define
        at least one service to continue""")

    deploy_graph = {}
    for service_name, service_definition in service_definitions.iteritems():
        deploy_graph[service_name] = set(service_definition.get('dependencies', {}))

    deploy_graph = list(toposort_flatten(deploy_graph))

    # Iterate over the deployment graph and start a microcosm process for each service described. This code is a little
    # clumsy right now because we're retrofitting microcosmctl.py to work with microcosm.py by using it's config file.

    port = 5000
    pid_map = {}
    for service_name in deploy_graph:
        service_config = {
            'service': str(service_name),
            'version': str(service_definitions[service_name].get('version', '1.0')),
            'dependencies': service_definitions[service_name].get('dependencies', []),
            'http_service': {
                'address': '127.0.0.1',
            }
        }

        service_config_file = arch_state_dir + '/' + service_name + '.yml'
        with open(service_config_file, 'w+') as f:
            yaml.dump(service_config, f)

        count = service_definitions[service_name].get('count', 1)
        for i in range(count):
            logger.info("Starting service instance (name: %s, port: %s)", service_name, port)
            log_file = open(arch_state_dir + "/logs/" + service_name + "." + str(i) + ".log", "w+")
            proc = subprocess.Popen([sys.executable, 'microcosm.py', '--http-port=' + str(port), service_config_file],
                                    env=os.environ.copy(),
                                    shell=False,
                                    stdout=log_file,
                                    stderr=subprocess.STDOUT,
                                    preexec_fn=os.setpgrp,
                                    close_fds=True,
                                    universal_newlines=True)

            if service_name not in pid_map:
                pid_map[service_name] = [{'pid': proc.pid}]
            else:
                pid_map[service_name].append({'pid': proc.pid})

            port += 1

    arch_state['running_services'] = pid_map
    update_state(arch['name'], arch_state)


def run_controller(args):
    arch = None
    arch_name = args.get('<architecture-name>', None)
    if args['<architecture-file>']:
        arch_file = args['<architecture-file>']
        arch_name = os.path.splitext(os.path.basename(arch_file))[0]
        logger.info("Loading architecture: %s", arch_name)
        arch = load_architecture(arch_file)
        arch['name'] = arch_name

    arch_state_dir = setup_state_dir(arch_name)
    arch_state_file = "{}/state.json".format(arch_state_dir)
    arch_state = {}
    with open(arch_state_file, 'r') as f:
        arch_state = json.load(f)

    if args['create']:
        create(args, arch, arch_state, arch_state_dir)
    elif args['destroy']:
        destroy(args, arch_state)
    elif args['refresh']:
        pass

    exit()


def main():
    exit(run_controller(docopt(__doc__, version='microcosmctl.py 0.0.1')))


if __name__ == "__main__":
    main()
