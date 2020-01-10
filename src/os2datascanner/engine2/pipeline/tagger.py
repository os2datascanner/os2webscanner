from os import getpid

from ...utils.metadata import guess_responsible_party
from ...utils.prometheus import prometheus_session
from ..model.core import Handle, SourceManager, ResourceUnavailableError
from .utilities import (notify_ready, pika_session, notify_stopping,
        prometheus_summary, json_event_processor, make_common_argument_parser)

args = None


@prometheus_summary(
        "os2datascanner_pipeline_tagger", "Metadata extractions")
@json_event_processor
def message_received(body, channel):
    handle = Handle.from_json_object(body["handle"])

    with SourceManager() as sm:
        try:
            yield (args.metadata, {
                "scan_tag": body["scan_tag"],
                "handle": body["handle"],
                "metadata": guess_responsible_party(handle, sm)
            })
        except ResourceUnavailableError as ex:
            print(ex)
            pass

def main():
    parser = make_common_argument_parser()
    parser.description = "Consume handles and generate metadata."

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--handles",
            metavar="NAME",
            help="the name of the AMQP queue from which handles"
                    + " should be read",
            default="os2ds_handles")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--metadata",
            metavar="NAME",
            help="the name of the AMQP queue to which metadata should be"
                    + " written",
            default="os2ds_metadata")

    global args
    args = parser.parse_args()

    with pika_session(args.handles, args.metadata,
            host=args.host, heartbeat=6000) as channel:
        channel.basic_consume(args.handles, message_received)

        with prometheus_session(
                str(getpid()),
                args.prometheus_dir,
                stage_type="tagger"):
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
