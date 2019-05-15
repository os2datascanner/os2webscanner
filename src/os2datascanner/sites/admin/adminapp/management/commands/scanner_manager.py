#!/usr/bin/env python

import json
import time
import logging

import pika

from django.core.management.base import BaseCommand

from os2datascanner.engine.run_webscan import StartWebScan
from os2datascanner.engine.run_filescan import StartFileScan



def callback(ch, method, properties, body):
    try:
        scan_job_list = []
        body = body.decode('utf-8')
        body = json.loads(body)
        print(" [x] Received %r" % body)
        # Collect scan object and map properties
        if body['type'] == 'WebScanner':
            scan_job_list.append(StartWebScan(body))
        else:
            scan_job_list.append(StartFileScan(body))
        scan_job_list[-1].start()
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        # reject the job; and delay so that we don't hog CPU
        logging.exception('failed to start scan job')
        ch.basic_reject(delivery_tag=method.delivery_tag)

        time.sleep(1)

class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '-H',
            '--amqp-host',
            type=str,
            default='localhost',
            help='Host name of the AMQP server',
        )
        parser.add_argument(
            '-Q',
            '--amqp-queue',
            type=str,
            default='datascanner',
            help='Queue to listen for changes',
        )

    def handle(self, amqp_queue, amqp_host, **kwargs):
        print(' [*] Waiting for messages. To exit press CTRL+C')

        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(amqp_host, heartbeat_interval=6000)
                )

                channel = connection.channel()

                channel.queue_declare(queue=amqp_queue)
                channel.basic_consume(callback, queue=amqp_queue)

                channel.start_consuming()
            except pika.exceptions.ConnectionClosed as exc:
                # the most frequent cause of sudden closures is VM
                # suspensions, but just in case, log it, back off a bit, and
                # resume
                print('AMQP connection closed:', exc)
                time.sleep(1)
