#!/usr/bin/env python
import pika
import json

from run import ScannerApp

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
    scan_job_list.append(ScannerApp(body['id'], body['type'], body["logfile"]))
    scan_job_list[-1].start()


channel.basic_consume(callback, queue=queue_name)


print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
