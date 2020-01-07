import pika

from .utilities import make_common_argument_parser


def main():
    parser = make_common_argument_parser()
    parser.description = "Consume all of the objeccs in a queue."

    parser.add_argument(
            "queue",
            nargs="+",
            choices=("os2ds_scan_specs", "os2ds_conversions",
                    "os2ds_representations", "os2ds_matches",
                    "os2ds_handles", "os2ds_metadata", "os2ds_problems",
                    "os2ds_results",),
            metavar="NAME",
            help="the AMQP queues from which objects should be read and"
                    " discarded",
            default=["os2ds_scan_specs"])

    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    for q in args.queue:
        channel.queue_purge(q)

    connection.close()


if __name__ == "__main__":
    main()
