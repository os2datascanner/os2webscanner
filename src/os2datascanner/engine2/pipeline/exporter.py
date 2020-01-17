from os import getpid
import json
import argparse

from ...utils.prometheus import prometheus_session
from ..model.core import (Handle,
        Source, UnknownSchemeError, DeserialisationError)
from .utilities import (notify_ready, pika_session, notify_stopping,
        prometheus_summary, json_event_processor, make_common_argument_parser)


def message_received_raw(body, channel, dump, results_q):
    body["origin"] = channel

    if "handle" in body:
        handle = Handle.from_json_object(body["handle"])
        handle = handle.censor()
        body["handle"] = handle.to_json_object()
    elif "where" in body:
        # Problem messages are a bit tricky to censor: we get a "where"
        # value that refers to the source of the problem, and we first need to
        # work out what it is
        where = body["where"]
        if "type" in where:
            # This is probably a Handle or a Source. Handles require more
            # structure, so try them first and then use Source as a fallback
            model_object = None
            try:
                model_object = Handle.from_json_object(where)
            except (DeserialisationError, UnknownSchemeError):
                try:
                    model_object = Source.from_json_object(where)
                except (DeserialisationError, UnknownSchemeError):
                    pass
            if model_object:
                where = model_object.censor().to_json_object()
        body["where"] = where

    if "scan_spec" in body:
        source = Source.from_json_object(body["scan_spec"]["source"])
        source = source.censor()
        body["scan_spec"]["source"] = source.to_json_object()

    # For debugging purposes
    if dump:
        print(json.dumps(body, indent=True))
        dump.write(json.dumps(body) + "\n")
        dump.flush()
        return

    yield (results_q, body)


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
            help="the name of the AMQP queue from which metadata should be"
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

    args = parser.parse_args()

    with pika_session(args.matches, args.problems, args.metadata, args.results,
            host=args.host, heartbeat=6000) as channel:

        @prometheus_summary(
                "os2datascanner_pipeline_exporter", "Messages exported")
        @json_event_processor
        def message_received(body, channel):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel, args.dump, args.results)
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


if __name__ == "__main__":
    main()
