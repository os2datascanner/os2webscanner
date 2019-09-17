import pika
from json import loads, dumps
from ..model.core import Source, SourceManager
from .utils import notify_ready, make_common_argument_parser

args = None

def message_received(channel, method, properties, body):
    print("message_received({0}, {1}, {2}, {3})".format(
            channel, method, properties, body))
    try:
        body = loads(body.decode("utf-8"))
        source = Source.from_json_object(body)

        with SourceManager() as sm:
            for handle in source.handles(sm):
                print(handle)
                channel.basic_publish(exchange='',
                        routing_key=args.conversions,
                        body=dumps(handle.to_json_object()).encode())

        channel.basic_ack(method.delivery_tag)
    except Exception:
        channel.basic_reject(method.delivery_tag)
        raise

def main():
    parser = make_common_argument_parser()
    parser.description = "Consume sources and generate conversions."

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--sources",
            metavar="NAME",
            help="the name of the AMQP queue from which scan specifications"
                    + " should be read",
            default="os2ds_sources")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue to which conversions should be"
                    + " written",
            default="os2ds_conversions")
    outputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue to which problems should be"
                    + " written",
            default="os2ds_problems")

    global args
    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.sources, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.conversions, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.problems, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.sources, message_received)

    try:
        print("Start")
        channel.start_consuming()
    finally:
        print("Stop")
        channel.stop_consuming()

if __name__ == "__main__":
    main()
