from os import getpid
import pika
from dateutil import tz

from ...utils.prometheus import prometheus_session
import ..rules._transitional_conversions
from ..rules.rule import Rule
from ..rules.types import convert, InputType, encode_dict, conversion_exists
from ..model.core import (Source,
        Handle, SourceManager, ResourceUnavailableError)
from .utilities import (notify_ready, notify_stopping, prometheus_summary,
        json_event_processor, make_common_argument_parser)

args = None
source_manager = None


def get_processor(sm, handle, required, configuration):
    if required == InputType.Text:
        resource = handle.follow(sm)
        mime_type = resource.compute_type()
        if "skip_mime_types" in configuration:
            for mt in configuration["skip_mime_types"]:
                if mt.endswith("*") and mime_type.startswith(mt[:-1]):
                    return None
                elif mime_type == mt:
                    return None
        if conversion_exists(InputType.Text, mime_type):
            return lambda handle: convert(handle.follow(sm), InputType.Text)
    elif required == InputType.LastModified:
        resource = handle.follow(sm)
        if hasattr(resource, "get_last_modified"):
            def _get_time(handle):
                return resource.get_last_modified()
            return _get_time
    return None


@prometheus_summary(
        "os2datascanner_pipeline_processor", "Representations generated")
@json_event_processor
def message_received(channel, method, properties, body):
    print("message_received({0}, {1}, {2}, {3})".format(
            channel, method, properties, body))
    try:
        handle = Handle.from_json_object(body["handle"])
        rule = Rule.from_json_object(body["progress"]["rule"])
        head, _, _ = rule.split()
        required = head.operates_on

        try:
            processor = get_processor(
                    source_manager, handle, required,
                    body["scan_spec"]["configuration"])
            if processor:
                representation = processor(handle)
                if representation:
                    yield (args.representations, {
                        "scan_spec": body["scan_spec"],
                        "handle": body["handle"],
                        "progress": body["progress"],
                        "representations": encode_dict({
                            required.value: representation
                        })
                    })
            else:
                # If we have a conversion we don't support, then check if
                # the current handle can be reinterpreted as a Source; if
                # it can, then try again with that
                derived_source = Source.from_handle(handle, source_manager)
                if derived_source:
                    # Copy almost all of the existing scan spec, but note the
                    # progress of rule execution and replace the source
                    scan_spec = body["scan_spec"].copy()
                    scan_spec["source"] = derived_source.to_json_object()
                    scan_spec["progress"] = body["progress"]
                    yield (args.sources, scan_spec)
        except ResourceUnavailableError:
            pass

        channel.basic_ack(method.delivery_tag)
    except Exception:
        channel.basic_reject(method.delivery_tag)
        raise


def main():
    parser = make_common_argument_parser()
    parser.description = ("Consume conversions and generate " +
            "representations and fresh sources.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue from which conversions"
                    + " should be read",
            default="os2ds_conversions")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--representations",
            metavar="NAME",
            help="the name of the AMQP queue to which representations"
                    + " should be written",
            default="os2ds_representations")
    outputs.add_argument(
            "--sources",
            metavar="NAME",
            help="the name of the AMQP queue to which scan specifications"
                    + " should be written",
            default="os2ds_scan_specs")

    global args
    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.conversions, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.representations, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.sources, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.conversions, message_received)

    global source_manager
    source_manager = SourceManager()

    with prometheus_session(
            str(getpid()),
            args.prometheus_dir,
            stage_type="processor"):
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
