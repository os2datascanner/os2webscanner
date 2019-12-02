#!/usr/bin/env python
import pika

from django.conf import settings

_amqp_obj = {
    "amqp_channels": None,
    "connection": None
}


def start_amqp(queue_name):
    """
    Starts an amqp connection and queue if it is not already started
    :param queue_name: Name of the queue
    """
    _create_connection()
    _create_channel(queue_name)


def _create_channel(queue_name):
    """
    Creates an amqp queue if a connection is created.
    :param queue_name: Name of the queue
    """
    if _amqp_obj['connection']:
        _amqp_obj['amqp_channel'] = _amqp_obj['connection'].channel()
        _amqp_obj['amqp_channel'].queue_declare(queue=queue_name,
                passive=False, durable=True,
                exclusive=False, auto_delete=False)


def _create_connection():
    """
    Creates a amqp connection
    """
    if not _amqp_obj['connection']:
        conn_params = pika.ConnectionParameters(settings.AMQP_HOST,
                                                heartbeat=6000)
        _amqp_obj['connection'] = pika.BlockingConnection(conn_params)


def send_message(routing_key, body):
    """
    Sends a message to the channel
    :return: None if no channel available
    """
    if _amqp_obj['amqp_channel']:
        _amqp_obj['amqp_channel'].basic_publish(exchange='',
                                                routing_key=routing_key,
                                                body=body)
    else:
        return None


def set_callback(func, queue_name):
    """
    Set callback on queue
    :param func: callback function
    :param queue_name: Name of the queue
    :return: None if no channel available
    """
    if _amqp_obj['amqp_channel']:
        _amqp_obj['amqp_channel'].basic_consume(func,
                                                queue=queue_name)
    else:
        return None


def start_consuming():
    if _amqp_obj['amqp_channel']:
        _amqp_obj['amqp_channel'].start_consuming()


def close_connection():
    """
    Closes the connection if connection is created
    """
    if _amqp_obj['connection']:
        _amqp_obj['connection'].close()
        _amqp_obj['connection'] = None
