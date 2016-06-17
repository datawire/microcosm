#!/usr/bin/env python

import requests

from discovery import Discovery, Node
from datawire_introspection import Platform, DatawireToken
from flask import Flask, jsonify
from uuid import uuid4

config = {}
depends_on = []
discovery = Discovery()

app = Flask(__name__)


def is_foundational():
    return len(config.get('dependencies', [])) == 0


@app.route('/', methods=['POST'])
def process_request():
    request_id = str(uuid4())
    app.logger.info("RECV REQUEST (id: {})", )
    result = []

    if is_foundational():
        result.append({'request_id': request_id})
    else:
        for service in config.get('dependencies'):
            address = discovery.resolve(service)
            response = requests.post('http://{}/'.format(address))
            app.logger.info("RECV RESPONSE")
            result.append(response.json)

    app.logger.info("SENT RESPONSE")
    return jsonify(result)


if __name__ == '__main__':
    app.debug = False

    import json

    with open('microcosm.json') as config_file:
        config = json.load(config_file)

    service_host = Platform.getRoutableHost()
    service_port = Platform.getRoutablePort(config.get('port'))

    datawire_config = config.get('datawire')

    discovery.withToken(datawire_config.get('discoveryToken', DatawireToken.getToken()))
    discovery.connectTo(datawire_config.get('discoveryAddress'))

    node = Node()
    node.service = config.get('service')
    node.address = '{}:{}'.format(service_host, service_port)
    node.version = config.get('version')

    discovery.start()
    discovery.register(node)

    import logging
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    logging.basicConfig(level=logging.INFO)

    app.run(host=config.get('host', '0.0.0.0'), port=config.get('port'))
