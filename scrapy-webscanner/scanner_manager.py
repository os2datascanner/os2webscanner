#!/usr/bin/env python
import pika
import json

from run import ScannerApp
from exchangescan.exchange_filescan import ExchangeFilescanner

queue_name = 'datascanner'


connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat_interval=6000))
channel = connection.channel()

channel.queue_declare(queue=queue_name)


def callback(ch, method, properties, body):
    body = body.decode('utf-8')
    body = json.loads(body)
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    # Collect scan object and map properties
    if body['type'] == 'ExchangeScanner':
        print('Starting exchange scanner.')
        exchange_scanner = ExchangeFilescanner(body['id'])
        exchange_scanner.start()
    else:
        scanner_app = ScannerApp(body['id'], body["logfile"])
        scanner_app.start()


channel.basic_consume(callback, queue=queue_name)


print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
