from dateutil import tz
import pika

from ..rules.rule import Rule
from ..rules.types import InputType
from ..rules.last_modified import DATE_FORMAT # XXX FIXME XXX
from ..model.core import (Source,
        Handle, SourceManager, ResourceUnavailableError)
from ..demo import processors
from .utilities import (notify_ready, notify_stopping, json_event_processor,
        make_common_argument_parser)

args = None
source_manager = None


def get_processor(sm, handle, required):
    if required == InputType.Text:
        resource = handle.follow(sm)
        mime_type = resource.compute_type()
        processor = processors.processors.get(mime_type)
        if processor:
            return lambda handle: processor(handle.follow(sm))
    elif required == InputType.LastModified:
        resource = handle.follow(sm)
        if hasattr(resource, "get_last_modified"):
            def _get_time(handle):
                r = handle.follow(sm)
                lm = r.get_last_modified()
                if not lm.tzname():
                    lm = lm.astimezone(tz.gettz())
                return lm.strftime(DATE_FORMAT)
            return _get_time
    return None


@json_event_processor
def message_received(channel, method, properties, body):
    print("message_received({0}, {1}, {2}, {3})".format(
            channel, method, properties, body))
    try:
        handle = Handle.from_json_object(body["handle"])
        rule = Rule.from_json_object(body["progress"]["rule"])
        head, _, _ = rule.split()

        try:
            processor = get_processor(source_manager, handle, head.operates_on)
            if processor:
                content = processor(handle)
                if content:
                    yield (args.representations, {
                        "scan_spec": body["scan_spec"],
                        "handle": body["handle"],
                        "progress": body["progress"],
                        "representation": {
                            "type": head.operates_on.value,
                            "content": content
                        }
                    })
            else:
                # If we have a conversion we don't support, then check if
                # the current handle can be reinterpreted as a Source; if
                # it can, then try again with that
                derived_source = Source.from_handle(handle, source_manager)
                if derived_source:
                    yield (args.sources, {
                        # Preserve the scan_tag value to indicate that this
                        # "new" scan is part of an existing one
                        "scan_tag": body["scan_spec"]["scan_tag"],
                        "source": derived_source.to_json_object(),
                        "progress": body["progress"]
                    })
        except ResourceUnavailableError as ex:
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
