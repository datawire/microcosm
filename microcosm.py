#!/usr/bin/env python

import requests
import sys

from discovery import Discovery, Node
from datawire_introspection import Platform, DatawireToken
from flask import Flask, jsonify
from uuid import uuid4

config = {}
depends_on = []
discovery = Discovery()

app = Flask(__name__)

NODE_REGISTERED              = "*** node started        (service: %s, version: %s)"
RECV_REQUEST_MSG             = "--> request             (id: %s)"
RECV_DOWNSTREAM_RESPONSE_MSG = "--> downstream response (id: %s)"
SENT_RESPONSE_MSG            = "<-- response            (id: %s)"


# TODO: Remove once Discovery client can resolve versions properly.
def create_service_name(name, version):
    return "{}:{}".format(name, version)


def is_foundational():
    return len(config.get('dependencies', [])) == 0


@app.route('/', methods=['POST'])
def process_request():
    request_id = str(uuid4())
    app.logger.info(RECV_REQUEST_MSG, request_id)
    result = []

    if is_foundational():
        result.append({'request_id': request_id})
    else:
        for service in config.get('dependencies'):
            address = discovery.resolve(service).address
            response = requests.post('http://{}/'.format(address))
            responder_data = response.json()
            responder_node = responder_data[0]
            app.logger.info(RECV_DOWNSTREAM_RESPONSE_MSG, responder_node['request_id'])
            result = result + responder_data

    app.logger.info(SENT_RESPONSE_MSG, request_id)
    return jsonify(result)


if __name__ == '__main__':
    app.debug = False

    import logging
    for logger_name in ['werkzeug', 'quark.discovery', 'requests', 'urllib3']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    import json
    with open(sys.argv[1]) as config_file:
        config = json.load(config_file)

    service_host = Platform.getRoutableHost()
    service_port = Platform.getRoutablePort(config.get('port'))

    datawire_config = config.get('datawire')

    discovery.withToken(datawire_config.get('discoveryToken', DatawireToken.getToken()))
    discovery.connectTo(datawire_config.get('discoveryAddress'))

    node = Node()
    # Hack to work around lack of version support in the client. Make the name <service>:<version>
    service_name = config.get('service')
    service_version = config.get('version')

    node.service = create_service_name(service_name, service_version)
    node.address = '{}:{}'.format(service_host, service_port)
    node.version = config.get('version')

    discovery.start()
    discovery.register(node)
    app.logger.info(NODE_REGISTERED, service_name, service_version)

    app.run(host=config.get('host', '0.0.0.0'), port=config.get('port'))
