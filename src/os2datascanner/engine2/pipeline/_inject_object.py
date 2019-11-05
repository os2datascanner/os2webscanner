import pika
from json import dumps, loads

from ..model.core import Source
from ..rules.cpr import CPRRule
from .utilities import make_common_argument_parser


def main():
    parser = make_common_argument_parser()
    parser.description = "Inject objects into a queue."

    parser.add_argument(
            "-S", "--scan-spec",
            nargs=2,
            metavar=("SOURCE-URL", "SCAN-TAG"),
            help="a scan specification to inject")
    parser.add_argument(
            "-J", "--json",
            metavar="OBJECT",
            help="a JSON object to inject")

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

    obj = None
    if args.scan_spec:
        url, tag = args.scan_spec
        obj = {
            "scan_tag": tag,
            "source": Source.from_url(url).to_json_object(),
            "rule": CPRRule().to_json_object()
        }
    elif args.json:
        obj = loads(args.json)

    if obj:
        channel.basic_publish(exchange='',
                routing_key=args.queue,
                body=dumps(obj).encode())

    connection.close()


if __name__ == "__main__":
    main()
