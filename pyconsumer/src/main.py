# -*- coding: utf-8 -*-

import argparse
import datetime
import json
import logging
import time
import pika
import sys
from yaml import load, YAMLError


settings = dict()

LOGGER = logging.getLogger('app')


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


class ExampleConsumer(object):

    def __init__(self, amqp_url):
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self.queue = settings['rabbitmq']['queuename']


    def connect(self):
        LOGGER.info('Connecting to %s', self._url)
        return pika.SelectConnection(pika.URLParameters(self._url),
                                     self.on_connection_open,
                                     stop_ioloop_on_close=False)


    def on_connection_open(self, unused_connection):
        LOGGER.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()


    def add_on_connection_close_callback(self):
        LOGGER.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)


    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)


    def reconnect(self):
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:
            # Create a new connection
            self._connection = self.connect()

            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()


    def open_channel(self):
        LOGGER.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)


    def on_channel_open(self, channel):
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchanges()


    def add_on_channel_close_callback(self):
        LOGGER.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)


    def on_channel_closed(self, channel, reply_code, reply_text):
        LOGGER.warning('Channel %i was closed: (%s) %s',
                       channel, reply_code, reply_text)
        self._connection.close()


    def setup_exchanges(self):
        LOGGER.info('Declaring exchanges')
        exchanges_def = settings['rabbitmq']['exchanges']
        for idx, exchange in enumerate(exchanges_def):
            # single callback for the last exchange setup
            callback = self.on_exchange_declareok if (idx == len(exchanges_def) - 1) else None
            self._channel.exchange_declare(callback, **exchange)


    def on_exchange_declareok(self, unused_frame):
        LOGGER.info('Exchange declared')
        self.setup_queues()


    def setup_queues(self):
        LOGGER.info('Declaring queues')
        queues_def = settings['rabbitmq']['queues']
        for idx, queue in enumerate(queues_def):
             # single callback for the last queue setup
             callback = self.on_queue_declareok if (idx == len(queues_def) - 1) else None
             self._channel.queue_declare(callback, **queue)


    def on_queue_declareok(self, method_frame):
        LOGGER.info('Bindings')
        bindings_def = settings['rabbitmq']['bindings']
        for idx, binding in enumerate(bindings_def):
            # single callback for the last binding setup
            callback = self.on_bindok if (idx == len(bindings_def) - 1) else None
            self._channel.queue_bind(self.on_bindok, **binding)


    def on_bindok(self, unused_frame):
        LOGGER.info('Queue bound')
        self.start_consuming()


    def start_consuming(self):
        LOGGER.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.queue)


    def add_on_cancel_callback(self):
        LOGGER.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)


    def on_consumer_cancelled(self, method_frame):
        LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()


    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        """
        LOGGER.info('Received message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)
        self.acknowledge_message(basic_deliver.delivery_tag)


    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        LOGGER.info('Acknowledging message %s', delivery_tag)
        self._channel.basic_ack(delivery_tag)


    def stop_consuming(self):
        if self._channel:
            LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)


    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame

        """
        LOGGER.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()


    def close_channel(self):
        LOGGER.info('Closing the channel')
        self._channel.close()


    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()


    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        LOGGER.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        LOGGER.info('Stopped')


    def close_connection(self):
        LOGGER.info('Closing connection')
        self._connection.close()


def main(amqp_url):
    #logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    example = ExampleConsumer(amqp_url)
    try:
        example.run()
    except KeyboardInterrupt:
        example.stop()


if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-stdout", "--stdout", action="store_true", default=False, help="Increase output verbosity")
    parser.add_argument("-configfile", "--configfile", required=True, help="Path to the yaml configfile")
    args = parser.parse_args()

    # Load the yaml configuration
    settings.update(load_settings(args.configfile))
    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger = logging.getLogger('app')
    logger.setLevel(settings['app']['log_level'])
    logger.addHandler(stdout_handler)

    # Init logger for pika
    logging.getLogger('pika').setLevel(logging.INFO)
    logging.getLogger('pika').addHandler(stdout_handler)

    # Ensure connexion with RabbitMQ
    logger.log(logging.INFO, msg='Connect to rabbitmq...')

    while True:
        try:
            #g_rabbitmq_cnx, g_rabbitmq_channel = rabbitmq_connect()
            logger.log(logging.INFO, "Connected with rabbitmq server.")
            break
        except (KeyboardInterrupt, SystemExit):
            sys.exit()
        except:
            logger.log(logging.INFO, "Waiting to connect rabbitmq server: sleep 1 sec...")
            time.sleep(1)

    # Consume messages
    amqp_url = 'amqp://{login}:{password}@{hostname}:{tcp_port}/%2F'.format(login=settings['rabbitmq']['username'], 
                                                                            password=settings['rabbitmq']['password'],
                                                                            hostname=settings['rabbitmq']['hostname'],
                                                                            tcp_port=settings['rabbitmq']['port'])
    main(amqp_url)

    logger.log(logging.INFO, "End program.")

