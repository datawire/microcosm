#!/usr/bin/env python

import requests

from flask import Flask, jsonify
from uuid import uuid4

node_id = str(uuid4())
depends_on = []

app = Flask(__name__)


def is_foundational():
    return len(depends_on) == 0


@app.route('/', methods=['POST'])
def process_request():
    request_id = str(uuid4())
    app.logger.info("RECV REQUEST (id: {})", )
    result = []

    if is_foundational():
        result.append({'request_id': request_id})
    else:
        for service in depends_on:
            address = 'localhost'
            response = requests.post('http://{}/'.format(address))
            app.logger.info("RECV RESPONSE")
            result.append(response.json)

    app.logger.info("SENT RESPONSE")
    return jsonify(result)


if __name__ == '__main__':
    app.debug = False

    import logging
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    logging.basicConfig(level=logging.INFO)

    app.run(host='0.0.0.0')
