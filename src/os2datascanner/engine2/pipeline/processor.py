from os import getpid

from ...utils.prometheus import prometheus_session
from ..rules.rule import Rule
from ..model.core import (Source,
        Handle, SourceManager, ResourceUnavailableError)
from ..conversions import convert
from ..conversions.types import OutputType, encode_dict
from ..conversions.utilities.results import SingleResult
from .utilities import (notify_ready, pika_session, notify_stopping,
        prometheus_summary, json_event_processor, make_common_argument_parser,
        make_sourcemanager_configuration_block)


def message_received_raw(
        body, channel, source_manager, representations_q, sources_q):
    handle = Handle.from_json_object(body["handle"])
    configuration = body["scan_spec"]["configuration"]
    rule = Rule.from_json_object(body["progress"]["rule"])
    head, _, _ = rule.split()
    required = head.operates_on

    try:
        resource = handle.follow(source_manager)

        representation = None
        if (required == OutputType.Text
                and "skip_mime_types" in configuration):
            mime_type = resource.compute_type()
            for mt in configuration["skip_mime_types"]:
                if mt.endswith("*") and mime_type.startswith(mt[:-1]):
                    break
                elif mime_type == mt:
                    break
            else:
                representation = convert(resource, OutputType.Text)
        else:
            representation = convert(resource, required)

        if representation and representation.parent:
            # If the conversion also produced other values at the same
            # time, then include all of those as well; they might also be
            # useful for the rule engine
            dv = {k.value: v.value
                    for k, v in representation.parent.items()
                    if isinstance(k, OutputType)}
        else:
            dv = {required.value: representation.value
                    if representation else None}

        yield (representations_q, {
            "scan_spec": body["scan_spec"],
            "handle": body["handle"],
            "progress": body["progress"],
            "representations": encode_dict(dv)
        })
    except KeyError:
        # If we have a conversion we don't support, then check if the current
        # handle can be reinterpreted as a Source; if it can, then try again
        # with that
        derived_source = Source.from_handle(handle, source_manager)
        if derived_source:
            # Copy almost all of the existing scan spec, but note the progress
            # of rule execution and replace the source
            scan_spec = body["scan_spec"].copy()
            scan_spec["source"] = derived_source.to_json_object()
            scan_spec["progress"] = body["progress"]
            yield (sources_q, scan_spec)
        else:
            # If we can't recurse any deeper, then produce an empty conversion
            # so that the matcher stage has something to work with
            # (XXX: is this always the right approach?)
            yield (representations_q, {
                "scan_spec": body["scan_spec"],
                "handle": body["handle"],
                "progress": body["progress"],
                "representations": {
                    required.value: None
                }
            })
    except ResourceUnavailableError:
        pass


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

    make_sourcemanager_configuration_block(parser)

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

    args = parser.parse_args()

    with pika_session(args.sources, args.conversions, args.representations,
            host=args.host, heartbeat=6000) as channel:
        with SourceManager(width=args.width) as source_manager:

            @prometheus_summary("os2datascanner_pipeline_processor",
                    "Representations generated")
            @json_event_processor
            def message_received(body, channel):
                if args.debug:
                    print(channel, body)
                return message_received_raw(body, channel,
                        source_manager, args.representations, args.sources)
            channel.basic_consume(args.conversions, message_received)

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


if __name__ == "__main__":
    main()
