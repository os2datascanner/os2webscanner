import pika

from .utils import notify_ready, notify_stopping, make_common_argument_parser

def message_received(channel, method, properties, body):
    print("message_received({0}, {1}, {2}, {3})".format(
            channel, method, properties, body))
    channel.basic_ack(method.delivery_tag)

def main():
    parser = make_common_argument_parser()
    parser.description = "Consume all of the objeccs in a queue."

    parser.add_argument(
            "--queue",
            choices=("os2ds_sources", "os2ds_conversions",
                    "os2ds_representations", "os2ds_matches",
                    "os2ds_handles", "os2ds_metadata", "os2ds_problems",),
            metavar="NAME",
            help="the name of the AMQP queue to which an object should be"
                    + " written",
            default="os2ds_sources")

    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.queue, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.queue, message_received)

    try:
        print("Start")
        notify_ready()
        channel.start_consuming()
    finally:
        print("Stop")
        notify_stopping()
        channel.stop_consuming()
        connection.close()

    connection.close()

if __name__ == "__main__":
    main()
