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

"""microcosm.py

Usage:
    microcosm.py [options] <config>
    microcosm.py (-h | --help)
    microcosm.py --version

Options:
    --http-port <port>  The http port to listen on.
    --http-addr <addr>  The http address to bind to [default: 127.0.0.1].
    -h --help           Show the help.
    --version           Show the version.
"""

import logging
import os
import re
import requests
import yaml

from discovery import Discovery, Node
from docopt import docopt
from datawire_introspection import Platform, DatawireToken
from flask import Flask, jsonify, request
from uuid import uuid4

dependencies = []
discovery = Discovery()
node_id = None

app = Flask(__name__)

NODE_REGISTERED              = "*** node started        (service: %s, version: %s, addr: %s)"
NODE_DEPENDS_ON              = "*** node depends on     (%s)"
RECV_REQUEST_MSG             = "--> request             (id: %s)"
SENT_DOWNSTREAM_REQUEST      = "--> downstream request  (service: %s, version: %s, addr: %s)"
RECV_DOWNSTREAM_RESPONSE_MSG = "--> downstream response (id: %s)"
SENT_RESPONSE_MSG            = "<-- response            (id: %s)"


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


def disable_noisy_loggers(loggers):
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)


def configure_dependencies(deps):
    global dependencies
    if isinstance(deps, basestring):
        if deps:
            dependencies = deps.split(",")
        else:
            pass
    elif isinstance(deps, list):
        dependencies = deps
    else:
        raise TypeError("Invalid config 'dependencies' format. Must either be a list or comma-separated string.")


def is_foundational():
    return len(dependencies) == 0


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/', methods=['POST', 'GET'])
def process_request():
    request_id = str(uuid4())
    app.logger.info(RECV_REQUEST_MSG, request_id)

    result = {
        'node_id': node_id,
        'request_id': request_id,
        'requests': []
    }

    for service in dependencies:
        node = discovery.resolve(service)
        node.await(10.0)
        response = requests.post('http://{}/'.format(node.address))
        app.logger.info(SENT_DOWNSTREAM_REQUEST, node.service, node.version, node.address)
        responder_data = response.json()
        app.logger.info(RECV_DOWNSTREAM_RESPONSE_MSG, responder_data['request_id'])
        result['requests'].append(responder_data)

    app.logger.info(SENT_RESPONSE_MSG, request_id)
    return jsonify(result)


def run_server(args):

    config_file = args['<config>']
    config = load_config(config_file)

    disable_noisy_loggers(['werkzeug', 'quark.discovery', 'requests', 'urllib3'])
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    configure_dependencies(config.get('dependencies', []))

    # These are the host and port the HTTP server is listening on and not the routable host and port
    httpd_config = config.get('http_server', {})
    httpd_addr = httpd_config.get('address', '0.0.0.0')
    httpd_port = int(httpd_config.get('port', args.get('--http-port', 5000)))

    service_host = Platform.getRoutableHost()
    service_port = Platform.getRoutablePort(httpd_port)

    discovery.withToken(DatawireToken.getToken())

    node = Node()
    service_name = config.get('service')
    service_version = str(config.get('version'))
    node.service = service_name

    node.address = '{}:{}'.format(service_host, service_port)
    node.version = config.get('version')

    global node_id
    node_id = "%s[%s, %s]" % (node.service, node.address, node.version)

    discovery.connect().start()
    discovery.register(node)
    app.logger.info(NODE_REGISTERED, service_name, service_version, node.address)

    if not is_foundational():
        app.logger.info(NODE_DEPENDS_ON, ", ".join(dependencies))

    app.run(host=httpd_addr, port=httpd_port, debug=False)


def main():
    exit(run_server(docopt(__doc__, version="microcosm.py 0.0.1")))


if __name__ == '__main__':
    main()
