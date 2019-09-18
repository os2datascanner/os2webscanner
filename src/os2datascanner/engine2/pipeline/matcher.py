import pika
from .utils import notify_ready, notify_stopping, make_common_argument_parser

def message_received(channel, method, properties, body):
    print("message_received({0}, {1}, {2}, {3})".format(
            channel, method, properties, body))
    try:
        channel.basic_ack(method.delivery_tag)
    except Exception:
        channel.basic_reject(method.delivery_tag)
        raise

def main():
    parser = make_common_argument_parser()
    parser.description = ("Consume representations and generate matches"
            + " and fresh conversions.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--representations",
            metavar="NAME",
            help="the name of the AMQP queue from which representations"
                    + " should be read",
            default="os2ds_representations")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--matches",
            metavar="NAME",
            help="the name of the AMQP queue to which matches should be"
                    + " written",
            default="os2ds_matches")
    outputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue to which conversions should be"
                    + " written",
            default="os2ds_conversions")
    outputs.add_argument(
            "--handles",
            metavar="NAME",
            help="the name of the AMQP queue to which handles (for metadata"
                    + " extraction) should be written",
            default="os2ds_handles")

    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.representations, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.matches, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.conversions, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.handles, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.representations, message_received)

    try:
        print("Start")
        notify_ready()
        channel.start_consuming()
    finally:
        print("Stop")
        notify_stopping()
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    main()
