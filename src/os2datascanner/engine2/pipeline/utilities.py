import json
import argparse
import systemd.daemon
if systemd.daemon.booted():
    from systemd.daemon import notify as sd_notify
else:
    def sd_notify(status):
        return False

from ...utils.system_utilities import json_utf8_decode
from ...utils.amqp_connection_manager import send_message


def make_common_argument_parser():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            "--host",
            metavar="HOST",
            help="the AMQP host to connect to",
            default="localhost")
    return parser


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


def json_event_processor(listener):
    def _wrapper(channel, method, properties, body):
        decoded_body = json_utf8_decode(body)
        if decoded_body:
            for routing_key, message in listener(
                    channel, method, properties, decoded_body):
                send_message(routing_key=routing_key,
                             body=json.dumps(message).encode())

    return _wrapper
