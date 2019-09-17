import pika
from .utils import notify_ready, make_common_argument_parser

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
    parser.description = ("Consume conversions and generate " +
            "representations and fresh sources.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue from which conversions"
                    + " should be read",
            default="os2ds_conversions")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--representations",
            metavar="NAME",
            help="the name of the AMQP queue to which representations"
                    + " should be written",
            default="os2ds_representations")
    outputs.add_argument(
            "--sources",
            metavar="NAME",
            help="the name of the AMQP queue to which scan specifications"
                    + " should be written",
            default="os2ds_sources")

    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.conversions, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.representations, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.sources, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.conversions, message_received)

    try:
        print("Start")
        channel.start_consuming()
    finally:
        print("Stop")
        channel.stop_consuming()

if __name__ == "__main__":
    main()
