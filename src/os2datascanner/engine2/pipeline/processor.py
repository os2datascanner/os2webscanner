import pika

from ..rules.types import InputType
from ..model.core import (Source,
        Handle, SourceManager, ResourceUnavailableError)
from ..demo import processors
from .utilities import (notify_ready, notify_stopping, json_event_processor,
        make_common_argument_parser)

args = None


@json_event_processor
def message_received(channel, method, properties, body):
    print("message_received({0}, {1}, {2}, {3})".format(
            channel, method, properties, body))
    try:
        handle = Handle.from_json_object(body["handle"])

        with SourceManager() as sm:
            try:
                resource = handle.follow(sm)
                mime_type = resource.compute_type()

                processor_function = processors.processors.get(mime_type)
                if processor_function:
                    content = processor_function(resource)
                    if content:
                        yield (args.representations, {
                            "scan_spec": body["scan_spec"],
                            "handle": body["handle"],
                            "representation": {
                                "type": InputType.Text.value,
                                "content": content
                            }
                        })
                else:
                    # If we have a conversion we don't support, then check if
                    # the current handle can be reinterpreted as a Source; if
                    # it can, then try again with that
                    derived_source = Source.from_handle(handle, sm)
                    if derived_source:
                        yield (args.sources, {
                            # Preserve the scan_tag value to indicate that this
                            # "new" scan is part of an existing one
                            "scan_tag": body["scan_spec"]["scan_tag"],
                            "source": derived_source.to_json_object(),
                            "rule": body["scan_spec"]["rule"]
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
            default="os2ds_sources")

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
