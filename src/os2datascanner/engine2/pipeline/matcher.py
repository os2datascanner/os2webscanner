import pika

from ..rules.rule import Rule
from ..rules.types import InputType
from .utilities import (notify_ready, notify_stopping, json_event_processor,
        make_common_argument_parser)

args = None


@json_event_processor
def message_received(channel, method, properties, body):
    print("message_received({0}, {1}, {2}, {3})".format(
            channel, method, properties, body))
    try:
        progress = body["progress"]
        representations = body["representations"]
        rule = Rule.from_json_object(progress["rule"])

        new_matches = []

        # Keep executing rules for as long as we can with the representations
        # we have
        while not isinstance(rule, bool):
            head, pve, nve = rule.split()

            target_type = head.operates_on
            type_value = target_type.value
            if not type_value in representations:
                # We don't have this representation -- bail out
                break

            content = target_type.decode_json_object(
                    representations[type_value])

            matches = list(head.match(content))
            new_matches.append({
                "rule": head.to_json_object(),
                "matches": matches if matches else None
            })
            if matches:
                rule = pve
            else:
                rule = nve

        if isinstance(rule, bool):
            # We've come to a conclusion!
            yield (args.matches, {
                "scan_spec": body["scan_spec"],
                "handle": body["handle"],
                "matched": rule,
                "matches": progress["matches"] + new_matches
            })
            # Only trigger metadata scanning if the match succeeded
            if rule:
                yield (args.handles, {
                    "scan_tag": body["scan_spec"]["scan_tag"],
                    "handle": body["handle"]
                })
        else:
            # We need a new representation to continue
            yield (args.conversions, {
                "scan_spec": body["scan_spec"],
                "handle": body["handle"],
                "progress": {
                    "rule": rule.to_json_object(),
                    "matches": progress["matches"] + new_matches
                }
            })

        channel.basic_ack(method.delivery_tag)
    except Exception:
        channel.basic_reject(method.delivery_tag)
        raise


def main():
    parser = make_common_argument_parser()
    parser.description = ("Consume representations and generate matches"
            + " and fresh conversions.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--representations",
            metavar="NAME",
            help="the name of the AMQP queue from which representations"
                    + " should be read",
            default="os2ds_representations")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--matches",
            metavar="NAME",
            help="the name of the AMQP queue to which matches should be"
                    + " written",
            default="os2ds_matches")
    outputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue to which conversions should be"
                    + " written",
            default="os2ds_conversions")
    outputs.add_argument(
            "--handles",
            metavar="NAME",
            help="the name of the AMQP queue to which handles (for metadata"
                    + " extraction) should be written",
            default="os2ds_handles")

    global args
    args = parser.parse_args()

    parameters = pika.ConnectionParameters(host=args.host, heartbeat=6000)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(args.representations, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.matches, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.conversions, passive=False,
            durable=True, exclusive=False, auto_delete=False)
    channel.queue_declare(args.handles, passive=False,
            durable=True, exclusive=False, auto_delete=False)

    channel.basic_consume(args.representations, message_received)

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
