import pika
from ...engine.utils import run_django_setup
from .utils import notify_ready, notify_stopping, make_common_argument_parser

# Exporters are the only part of the pipeline allowed to use the database, and
# even only to write to it
run_django_setup()

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
    parser.description = ("Consume problems and matches and write them to the"
            + " database.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--matches",
            metavar="NAME",
            help="the name of the AMQP queue from which matches should be"
                    + " read",
            default="os2ds_matches")
    inputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue from which problems should be"
                    + " read",
            default="os2ds_problems")
    inputs.add_argument(
            "--metadata",
            metavar="NAME",
            help="the name of the AMQP queue from which matches should be"
                    + " read",
            default="os2ds_metadata")

    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.matches, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.problems, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.metadata, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.matches, message_received)
    channel.basic_consume(args.problems, message_received)
    channel.basic_consume(args.metadata, message_received)

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
