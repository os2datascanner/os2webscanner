import argparse

def make_common_argument_parser():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            "--host",
            metavar="HOST",
            help="the AMQP host to connect to",
            default="localhost")
    return parser

import systemd.daemon
if systemd.daemon.booted():
    from systemd.daemon import notify as sd_notify
else:
    sd_notify = lambda status: False

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
