from os import getpid
import json
import argparse

from ..model.core import Handle
from ...utils.prometheus import prometheus_session
from .utilities import (notify_ready, notify_stopping, prometheus_summary,
                        make_common_argument_parser, json_event_processor)
from ...utils.amqp_connection_manager import (start_amqp, ack_message,
                                              set_callback, start_consuming,
                                              close_connection)

args = None


@prometheus_summary("os2datascanner_pipeline_exporter", "Messages exported")
@json_event_processor
def message_received(channel, method, properties, body):
    ack_message(method)
    try:
        handle = Handle.from_json_object(body["handle"])
        handle = handle.censor()
        body = handle.to_json_object()
    except Exception:
        raise
    body['origin'] = method.routing_key
    # For debugging purposes
    if args.dump:
        print(json.dumps(body, indent=True))
        args.dump.write(body + "\n")
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

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--results",
            metavar="NAME",
            help="the name of the AMQP queue to which filtered result objects"
                    + " should be written",
            default="os2ds_results")
    outputs.add_argument(
            "--debug-dump",
            dest="dump",
            metavar="PATH",
            help="the name of a JSON Lines file to which all incoming messages"
                    + "should be dumped (existing content will be deleted!)",
            type=argparse.FileType(mode="wt"),
            default=None)

    global args
    args = parser.parse_args()

    # AMQP host is located in settings.
    start_amqp(args.matches)
    start_amqp(args.problems)
    start_amqp(args.metadata)
    start_amqp(args.results)

    set_callback(message_received, args.matches)
    set_callback(message_received, args.problems)
    set_callback(message_received, args.metadata)

    with prometheus_session(
            str(getpid()),
            args.prometheus_dir,
            stage_type="exporter"):
        try:
            print("Start")
            notify_ready()
            start_consuming()
        finally:
            print("Stop")
            notify_stopping()
            close_connection()


if __name__ == "__main__":
    main()
