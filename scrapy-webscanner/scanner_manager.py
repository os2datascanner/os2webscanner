#!/usr/bin/env python
import os
import sys
import django

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()

os.umask(0o007)

from run import ScannerApp
from os2webscanner.amqp_communication import amqp_connection_manager
queue_name = 'datascanner'

amqp_connection_manager.start_amqp(queue_name)


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    scanner_app = ScannerApp(body.decode('utf-8'))
    scanner_app.run()


amqp_connection_manager.set_callback(callback, queue_name)

print(' [*] Waiting for messages. To exit press CTRL+C')
amqp_connection_manager.start_consuming()
