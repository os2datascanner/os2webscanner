import json
import argparse

from nested_lookup import nested_delete

from .utilities import (notify_ready, json_event_processor,
        notify_stopping, make_common_argument_parser)
from ...utils.system_utilities import json_utf8_decode
from ...utils.amqp_connection_manager import start_amqp, \
    ack_message, set_callback, start_consuming, close_connection

args = None

@json_event_processor
def message_received(channel, method, properties, body):
    ack_message(channel, method)

    decoded_body = json_utf8_decode(body)
    if decoded_body:
        # For debugging purposes
        if args.dump:
            print(json.dumps(decoded_body, indent=True))
            args.dump.write(decoded_body + "\n")
            args.dump.flush()
            return

        filtered_body = filter_message(decoded_body)
        yield (args.results, filtered_body)

def filter_message(decoded_body):
    # send filtered body.
    # username and password should be removed
    # and dataqueue-type data needs to be added.
    decoded_body = nested_delete(decoded_body, 'user')
    decoded_body = nested_delete(decoded_body, 'password')

    return decoded_body

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
