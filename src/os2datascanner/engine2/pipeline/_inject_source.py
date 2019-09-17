import pika
from json import dumps

from ..model.core import Source, SourceManager, UnknownSchemeError
from .utils import notify_ready, make_common_argument_parser

def main():
    parser = make_common_argument_parser()
    parser.description = "Consume sources and generate conversions."

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            metavar="URL",
            dest="urls",
            nargs="+",
            help="one or more")

    outputs = parser.add_argument_group("inputs")
    outputs.add_argument(
            "--sources",
            metavar="NAME",
            help="the name of the AMQP queue to which a scan specification"
                    + " should be written",
            default="os2ds_sources")

    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.sources, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    for i in args.urls:
        try:
            s = Source.from_url(i)
            channel.basic_publish(exchange='',
                    routing_key=args.sources,
                    body=dumps(s.to_json_object()).encode())
        except UnknownSchemeError:
            pass

    connection.close()

if __name__ == "__main__":
    main()
