from os import getpid
import json
import pika
import argparse

from ..model.core import Handle, Source
from ...utils.prometheus import prometheus_session
from .utilities import (notify_ready, notify_stopping, prometheus_summary,
                        make_common_argument_parser, json_event_processor)

args = None


@prometheus_summary("os2datascanner_pipeline_exporter", "Messages exported")
@json_event_processor
def message_received(channel, method, properties, body):
    channel.basic_ack(method.delivery_tag)

    handle = Handle.from_json_object(body["handle"])
    handle = handle.censor()
    body['handle'] = handle.to_json_object()
    body['origin'] = method.routing_key

    # Also censor the scan specification's source, if this type of message
    # carries one
    if "scan_spec" in body:
        source = Source.from_json_object(body["scan_spec"]["source"])
        source = source.censor()
        body["scan_spec"]["source"] = source.to_json_object()

    # For debugging purposes
    if args.dump:
        print(json.dumps(body, indent=True))
        args.dump.write(json.dumps(body) + "\n")
        args.dump.flush()
        return

    yield (args.results, body)


def main():
    parser = make_common_argument_parser()
    parser.description = ("Consume problems, metadata and matches, and convert"
                          + " them into forms suitable for the outside world.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--matches",
            metavar="NAME",
            help="the name of the AMQP queue from which matches should be"
                    " read",
            default="os2ds_matches")
    inputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue from which problems should be"
                    " read",
            default="os2ds_problems")
    inputs.add_argument(
            "--metadata",
            metavar="NAME",
            help="the name of the AMQP queue from which matches should be"
                    " read",
            default="os2ds_metadata")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--results",
            metavar="NAME",
            help="the name of the AMQP queue to which filtered result objects"
                    " should be written",
            default="os2ds_results")
    outputs.add_argument(
            "--dump",
            metavar="PATH",
            help="the name of a JSON Lines file to which filtered result"
                    "objects should also be appended",
            type=argparse.FileType(mode="at"),
            default=None)

    global args
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
    channel.queue_declare(args.results, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.matches, message_received)
    channel.basic_consume(args.problems, message_received)
    channel.basic_consume(args.metadata, message_received)

    with prometheus_session(
            str(getpid()),
            args.prometheus_dir,
            stage_type="exporter"):
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
