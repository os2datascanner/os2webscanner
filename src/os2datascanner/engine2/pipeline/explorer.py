from os import getpid

from ...utils.prometheus import prometheus_session
from ..model.core import (Source, SourceManager, UnknownSchemeError,
        DeserialisationError, ResourceUnavailableError)
from .utilities import (notify_ready, pika_session, notify_stopping,
        prometheus_summary, json_event_processor, make_common_argument_parser,
        make_sourcemanager_configuration_block)


def message_received_raw(
        body, channel, source_manager, conversions_q, problems_q):
    try:
        source = Source.from_json_object(body["source"])

        # The configuration dictionary was added fairly late to scan specs, so
        # not all clients will send it. Add an empty one if necessary
        body.setdefault("configuration", {})

        if "progress" in body:
            # If this scan spec is based on a derived source and so contains
            # scan progress information, then take it out; the rest of the
            # pipeline won't look for it here
            progress = body["progress"]
            del body["progress"]
        else:
            progress = dict(rule=body["rule"], matches=[])
    except UnknownSchemeError as ex:
        yield (problems_q, {
            "where": body["source"],
            "problem": "unsupported",
            "extra": [str(arg) for arg in ex.args]
        })
        return
    except DeserialisationError as ex:
        yield (problems_q, {
            "where": body["source"],
            "problem": "malformed",
            "extra": [str(arg) for arg in ex.args]
        })
        return
    except KeyError as ex:
        yield (problems_q, {
            "where": body,
            "problem": "malformed",
            "extra": [str(arg) for arg in ex.args]
        })
        return

    try:
        for handle in source.handles(source_manager):
            try:
                print(handle.censor())
            except NotImplementedError:
                # If a Handle doesn't implement censor(), then that indicates
                # that it doesn't know enough about its internal state to
                # censor itself -- just print its type
                print("(unprintable {0})".format(type(handle).__name__))
            yield (conversions_q, {
                "scan_spec": body,
                "handle": handle.to_json_object(),
                "progress": progress
            })
    except ResourceUnavailableError as ex:
        yield (problems_q, {
            "where": body["source"],
            "problem": "unavailable",
            "extra": [str(arg) for arg in ex.args]
        })
    # Note that exceptions not caught and wrapped by engine2 will cause this
    # (and every other!) pipeline stage to abort unexpectedly. To trigger an
    # automatic restart in this case, use a service manager like systemd


def main():
    parser = make_common_argument_parser()
    parser.description = "Consume sources and generate conversions."

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--sources",
            metavar="NAME",
            help="the name of the AMQP queue from which scan specifications"
                    + " should be read",
            default="os2ds_scan_specs")

    make_sourcemanager_configuration_block(parser)

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue to which conversions should be"
                    + " written",
            default="os2ds_conversions")
    outputs.add_argument(
            "--problems",
            metavar="NAME",
            help="the name of the AMQP queue to which problems should be"
                    + " written",
            default="os2ds_problems")

    args = parser.parse_args()

    with pika_session(args.sources, args.conversions, args.problems,
            host=args.host, heartbeat=6000) as channel:
        with SourceManager(width=args.width) as source_manager:

            @prometheus_summary(
                    "os2datascanner_pipeline_explorer", "Sources explored")
            @json_event_processor
            def message_received(body, channel):
                if args.debug:
                    print(channel, body)
                return message_received_raw(body, channel,
                        source_manager, args.conversions, args.problems)
            channel.basic_consume(args.sources, message_received)

            with prometheus_session(
                    str(getpid()),
                    args.prometheus_dir,
                    stage_type="explorer"):
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
