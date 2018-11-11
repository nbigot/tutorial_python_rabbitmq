# -*- coding: utf-8 -*-

import argparse
import json
import logging
import pika
from datetime import datetime
from flask import Flask
from flask_cors import CORS
from uuid import uuid4
from yaml import load, YAMLError


app = Flask(__name__)

settings = dict()


def load_settings(filename: str) -> dict:
    with open(filename, mode='r', encoding='utf-8') as stream:
        try:
            return load(stream)
        except YAMLError as ex:
            logging.getLogger('config').error(ex)
            raise


def rabbitmq_connect():
    credentials = pika.PlainCredentials(
        username=settings['rabbitmq']['username'],
        password=settings['rabbitmq']['password'])
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings['rabbitmq']['hostname'],
            port=settings['rabbitmq']['port'],
            credentials=credentials))
    channel = connection.channel()
    return connection, channel


def rabbitmq_configure(config: dict) -> None:
    """Configure rabbitmq server"""
    connection, channel = rabbitmq_connect()

    # Declare the exchanges
    for exchange in config.get('exchanges'):
        channel.exchange_declare(**exchange)

    # Declare the queues
    for queue in config.get('queues'):
        channel.queue_declare(**queue)

    # Declare the bindings
    for binding in config.get('bindings'):
        channel.queue_bind(**binding)

    connection.close()


def rabbitmq_publish_message(exchange: str, routing_key: str, msg: str) -> None:
    connection, channel = rabbitmq_connect()
    channel.basic_publish(exchange=exchange, routing_key=routing_key, body=msg)
    connection.close()


@app.route('/')
def home():
    """Renders the home page."""
    return 'Please take a look at the web service documentation.'


@app.route('/ping', methods=['GET'])
def ping():
    """Service health check"""
    return 'pong', 200


@app.route('/hello/<string:name>', methods=['POST'])
def hello(name: str):
    """Create a new message and send it to Rabbitmq"""
    try:
        json_message = {
            'uid': str(uuid4()),
            'creation_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'say hello to': name
        }
        msg = json.dumps(json_message, ensure_ascii=False).encode("utf-8")
        rabbitmq_publish_message(exchange="exchange1", routing_key="hello_topic", msg=msg)
        return 'Added hello message to: {}'.format(name), 200
    except Exception as ex:
        return 'Error: {}'.format(ex), 500


@app.route('/custom/<string:routing_key>', methods=['POST'])
def custom(routing_key: str):
    """Create a new message and send it to Rabbitmq"""
    try:
        json_message = {
            'uid': str(uuid4()),
            'creation_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'name': 'custom routing_key: {}'.format(routing_key)
        }
        msg = json.dumps(json_message, ensure_ascii=False).encode("utf-8")
        rabbitmq_publish_message(exchange="exchange1", routing_key=routing_key, msg=msg)
        return 'Added message to specific routing_key: {}'.format(routing_key), 200
    except Exception as ex:
        return 'Error: {}'.format(ex), 500


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-stdout", "--stdout", action="store_true", default=False, help="Increase output verbosity")
    parser.add_argument("-configfile", "--configfile", required=True, help="Path to the yaml configfile")
    args = parser.parse_args()

    # Load the yaml configuration
    global settings
    settings.update(load_settings(args.configfile))
    app.logger.setLevel(settings['app']['log_level'])

    # Ensure RabbitMQ config from the yaml config
    try:
        app.logger.log('INFO', event='configure rabbitmq', tags=['rabbitmq'])
        rabbitmq_configure(settings['rabbitmq'])
    except Exception as ex:
        app.logger.exception(ex=ex,
                             action='configure rabbitmq',
                             event='exception rabbitmq config',
                             tags=['exception', 'rabbitmq'])

    # Start web server
    CORS(app)
    app.logger.log('INFO', action='server start', tags=['server'])
    app.run(host=settings['app']['hostname'],
            port=settings['app']['tcp_port'],
            debug=settings['app']['flask_debug'])