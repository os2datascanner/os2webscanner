import json
import pika
import argparse
from contextlib import contextmanager
import systemd.daemon
if systemd.daemon.booted():
    from systemd.daemon import notify as sd_notify
else:
    def sd_notify(status):
        return False
from prometheus_client import Summary

from ...utils.system_utilities import json_utf8_decode


def make_common_argument_parser():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            "--host",
            metavar="HOST",
            help="the AMQP host to connect to",
            default="localhost")
    parser.add_argument(
            "--debug",
            action="store_true",
            help="print all incoming messages to the console")

    monitoring = parser.add_argument_group("monitoring")
    monitoring.add_argument(
            "--prometheus-dir",
            metavar="DIR",
            help="the directory in which to drop a Prometheus description"
                    " of this pipeline stage",
            default=None)

    return parser


def make_sourcemanager_configuration_block(parser):
    configuration = parser.add_argument_group("configuration")
    configuration.add_argument(
            "--width",
            type=int,
            metavar="SIZE",
            help="allow each source to have at most %(metavar) "
                    "simultaneous open sub-sources",
            default=3)

    return configuration


def notify_ready():
    sd_notify("READY=1")


def notify_reloading():
    sd_notify("RELOADING=1")


def notify_stopping():
    sd_notify("STOPPING=1")


def notify_status(msg):
    sd_notify("STATUS={0}".format(msg))


def notify_watchdog():
    sd_notify("WATCHDOG=1")


def prometheus_summary(*args):
    """Decorator. Records a Prometheus summary observation for every call to
    the decorated function."""
    s = Summary(*args)

    def _prometheus_summary(func):
        return s.time()(func)
    return _prometheus_summary


def json_event_processor(listener):
    """Decorator. Automatically decodes JSON bodies for the wrapped Pika
    message callback, and automatically produces new messages for every (queue
    name, serialisable object) pair yielded by that callback."""

    def _wrapper(channel, method, properties, body):
        channel.basic_ack(method.delivery_tag)
        decoded_body = json_utf8_decode(body)
        if decoded_body:
            for routing_key, message in listener(
                    decoded_body, channel=method.routing_key):
                channel.basic_publish(exchange='',
                        routing_key=routing_key,
                        body=json.dumps(message).encode())
    return _wrapper


@contextmanager
def pika_session(*queues, **kwargs):
    parameters = pika.ConnectionParameters(**kwargs)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    for q in queues:
        channel.queue_declare(q, passive=False,
                durable=True, exclusive=False, auto_delete=False)

    try:
        yield channel
    finally:
        connection.close()
