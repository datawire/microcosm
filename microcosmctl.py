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
    microcosmctl.py run  <architecture-file> [ --timeout=<seconds> ]
    microcosmctl.py (-h | --help)
    microcosmctl.py --version

Options:
    -h --help             Show the help.
    --version             Show the version.
    --timeout=<seconds>   Timeout in seconds.
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
import mdk
import atexit
import time

from collections import OrderedDict
from docopt import docopt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger('microcosmctl.py')

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

class Architecture:

    @staticmethod
    def load(path):
        """
        Reads a Microcosm configuration file.

        :param path: the path to the configuration file :return: a
        dictionary containing configuration values
        """
        name = os.path.splitext(os.path.basename(path))[0]
        return Architecture(name, load_yaml(path))

    def __init__(self, name, arch):
        self.name = name
        self.services = OrderedDict()
        svcs = arch.get("services", {}).items()
        if len(svcs) < 1:
            raise ValueError('Missing or empty "services" key. Define at least one service to continue')

        for name, dfn in svcs:
            self.services[name] = Service(self, name, dfn)
        for name, dfn in svcs:
            self.services[name]._deps(dfn.get("dependencies", []))
        self.state_dir = ".microcosm/{}".format(self.name)
        self.port = 5000

    def setup_state_dir(self):
        try:
            logger.info("Initializing architecture state directory (path: %s)", self.state_dir)
            os.makedirs(self.state_dir)
        except OSError:
            if not os.path.isdir(self.state_dir):
                raise

    def ordered(self):
        edges = []
        internal = []
        for svc in self.services.values():
            if svc.edge():
                edges.append(svc)
            else:
                internal.append(svc)
        return edges + internal

    def refresh(self, disco):
        for svc in self.ordered():
            cluster = disco.services.get(svc.name, None)
            if cluster:
                delta = svc.count - len(cluster.nodes)
            else:
                delta = svc.count

            for i in range(delta):
                svc.launch(self.port)
                self.port += 1


    def shutdown(self):
        for svc in self.services.values():
            svc.shutdown()

    def wait(self):
        for svc in self.services.values():
            svc.wait()

class Service:

    def __init__(self, arch, name, dfn):
        self.arch = arch
        self.name = name
        self.version = str(dfn.get("version", "1.0"))
        self.count = dfn.get("count", 1)
        self.processes = []

    def _deps(self, deps):
        self.dependencies = [self.arch.services[name] for name in deps]

    def edge(self):
        for c in self.clients():
            return False
        else:
            return True

    def clients(self):
        for svc in self.arch.services.values():
            if self in svc.dependencies:
                yield svc

    def shutdown(self):
        for proc in self.processes:
            proc.send_signal(signal.SIGINT)

    def wait(self):
        for proc in self.processes:
            logger.info("%s instance[%s] exited: %s", self.name, proc.pid, proc.wait())

    def config(self, port):
        return {
            'service': self.name,
            'version': self.version,
            'dependencies': [d.name for d in self.dependencies],
            'http_server': {
                'address': '127.0.0.1',
                'port': port
            }
        }

    def launch(self, port):
        logger.info("Launching %s[%s] on %s", self.name, self.version, port)
        config = self.config(port)

        config_file = os.path.join(self.arch.state_dir, "%s-%s.yml" % (self.name, port))
        with open(config_file, 'w+') as f:
            yaml.dump(config, f)

        log_file = open(os.path.join(self.arch.state_dir, "%s-%s.log" % (self.name, port)), "w+")

        proc = subprocess.Popen([sys.executable, 'microcosm.py', config_file],
                                env=os.environ.copy(),
                                shell=False,
                                stdout=log_file,
                                stderr=subprocess.STDOUT,
                                preexec_fn=os.setpgrp,
                                close_fds=True,
                                universal_newlines=True)

        pid_file = os.path.join(self.arch.state_dir, "%s-%s.pid" % (self.name, port))
        with open(pid_file, 'w+') as f:
            f.write("%s\n" % proc.pid)

        self.processes.append(proc)

def run(args):
    arch_file = args['<architecture-file>']
    logger.info("Loading architecture: %s", arch_file)
    arch = Architecture.load(arch_file)

    m = mdk.init()
    m.start()
    atexit.register(m.stop)
    disco = m._disco

    # Wait to learn about what is out there, this could be a lot
    # smarter and actually respawn stuff, but that can wait...
    timeout = float(args["--timeout"] or 3.0)
    time.sleep(timeout)

    arch.setup_state_dir()
    arch.refresh(disco)

    try:
        arch.wait()
    except KeyboardInterrupt:
        arch.shutdown()
        arch.wait()

def run_controller(args):
    if args['run']:
        run(args)
    else:
        assert False

    exit()


def main():
    exit(run_controller(docopt(__doc__, version='microcosmctl.py 0.0.1')))


if __name__ == "__main__":
    main()
