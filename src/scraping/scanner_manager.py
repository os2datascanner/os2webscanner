#!/usr/bin/env python

import json
import time

import pika

from .run_webscan import StartWebScan
from .run_filescan import StartFileScan


QUEUE_NAME = 'datascanner'


def callback(ch, method, properties, body):
    scan_job_list = []
    body = body.decode('utf-8')
    body = json.loads(body)
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    # Collect scan object and map properties
    if body['type'] == 'WebScanner':
        scan_job_list.append(StartWebScan(body))
    else:
        scan_job_list.append(StartFileScan(body))
    scan_job_list[-1].start()



print(' [*] Waiting for messages. To exit press CTRL+C')
while True:
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost',
                                      heartbeat_interval=6000)
        )

        channel = connection.channel()

        channel.queue_declare(queue=QUEUE_NAME)
        channel.basic_consume(callback, queue=QUEUE_NAME)

        channel.start_consuming()
    except pika.exceptions.ConnectionClosed as exc:
        # the most frequent cause of sudden closures is VM
        # suspensions, but just in case, log it, back off a bit, and
        # resume
        print('AMQP connection closed:', exc)
        time.sleep(1)
