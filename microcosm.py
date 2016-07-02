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
import mdk
import atexit

from docopt import docopt
from flask import Flask, jsonify, request
from uuid import uuid4

dependencies = []
m = mdk.init()
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
    context = request.headers.get("MDK-Context")
    if context:
        m.join_encoded_context(context)
    else:
        m.init_context()

    request_id = m.context().encode()
    m.info("upstream", RECV_REQUEST_MSG % request_id)

    result = {
        'node_id': node_id,
        'request_id': request_id,
        'requests': []
    }

    for service in dependencies:
        # XXX: we need to add versioning both to config and make
        # resolve pay attention to it
        node = m.resolve(service, "<ignored-version>")
        response = requests.post(node.address, headers={"MDK-Context": request_id})
        m.info("downstream", SENT_DOWNSTREAM_REQUEST % (node.service, node.version, node.address))
        responder_data = response.json()
        m.info("downstream", RECV_DOWNSTREAM_RESPONSE_MSG % responder_data['request_id'])
        result['requests'].append(responder_data)

    m.info("upstream", SENT_RESPONSE_MSG % request_id)
    return jsonify(result)

@app.errorhandler(Exception)
def unhandled_exception(e):
    import traceback
    m.error("exception", traceback.format_exc(e))
    return render_template('500.htm'), 500

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

    service = config.get('service')
    version = str(config.get('version'))
    address = 'http://{}:{}'.format(httpd_addr, httpd_port)

    global node_id
    node_id = "%s[%s, %s]" % (service, version, address)

    m.register(service, version, address)
    m.start()
    atexit.register(m.stop)

    m.info("boot", NODE_REGISTERED % (service, version, address))

    if not is_foundational():
        m.info("boot", NODE_DEPENDS_ON % ", ".join(dependencies))

    app.run(host=httpd_addr, port=httpd_port, debug=False)

def main():
    exit(run_server(docopt(__doc__, version="microcosm.py 0.0.1")))


if __name__ == '__main__':
    main()
