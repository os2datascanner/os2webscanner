#!/usr/bin/env python
import pika
import json

import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

os.umask(0o007)
os.environ["SCRAPY_SETTINGS_MODULE"] = "scanners.settings"

django.setup()

from run_webscan import StartWebScan
from run_filescan import StartFileScan


queue_name = 'datascanner'


connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost',
                              heartbeat_interval=6000)
)

channel = connection.channel()

channel.queue_declare(queue=queue_name)

scan_job_list = []


def callback(ch, method, properties, body):
    body = body.decode('utf-8')
    body = json.loads(body)
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    # Collect scan object and map properties
    if body['type'] == 'WebScanner':
        scan_job_list.append(StartWebScan(
                body['id'], body['logfile'], body['last_started']))
    else:
        scan_job_list.append(StartFileScan(
            body['id'], body['logfile'], body['last_started']))
    scan_job_list[-1].start()



channel.basic_consume(callback, queue=queue_name)


print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
