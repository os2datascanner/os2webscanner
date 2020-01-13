from    os import getenv
import  sys
from    json import dumps, loads
import  pika
import  base64
import  unittest

from    os2datascanner.engine2.pipeline import (
        explorer, processor, matcher, tagger, exporter)
from    os2datascanner.engine2.pipeline.utilities import json_event_processor
from    os2datascanner.engine2.model.core import Source
from    os2datascanner.engine2.rules.regex import RegexRule
from    os2datascanner.engine2.rules.logical import OrRule


data = """Hwæt! wē Gār-Dena in gēar-dagum
þēod-cyninga þrym gefrūnon,
hū ðā æþeling as ell en fremedon.
Oft Scyld Scēfing sceaþena þrēatum,
monegum mǣgþum meodo-setla oftēah."""
data_url = "data:text/plain;base64,{0}".format(
       base64.encodebytes(data.encode("utf-8")).decode("ascii"))

rule = OrRule(
        RegexRule("Æthelred the Unready"),
        RegexRule("Scyld S(.*)g"),
        RegexRule("Professor James Moriarty"))

expected_matches = [
    {
        "rule": {
            "type": "regex",
            "expression": "Æthelred the Unready"
        },
        "matches": None
    },
    {
        "rule": {
            "type": "regex",
            "expression": "Scyld S(.*)g"
        },
        "matches": [
            {
                "offset": 98,
                "match": "Scyld Scēfing"
            }
        ]
    }
]


class StopHandling(Exception):
    pass


@json_event_processor
def message_received(body, channel):
    if channel == "os2ds_scan_specs":
        return explorer.message_received_raw(body, channel,
                "os2ds_conversions", "os2ds_problems")
    elif channel == "os2ds_conversions":
        return processor.message_received_raw(body, channel,
                "os2ds_representations", "os2ds_scan_specs")
    elif channel == "os2ds_representations":
        return matcher.message_received_raw(body, channel,
                "os2ds_matches", "os2ds_handles", "os2ds_conversions")
    elif channel == "os2ds_handles":
        return tagger.message_received_raw(body, channel,
                "os2ds_metadata")
    elif channel in ("os2ds_matches", "os2ds_metadata", "os2ds_problems",):
        return exporter.message_received_raw(body, channel,
                False, "os2ds_results")


class Engine2PipelineTests(unittest.TestCase):
    def setUp(self):
        parameters = pika.ConnectionParameters(
                host=getenv("AMQP_HOST", "localhost"),
                heartbeat=6000)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        for c in ("os2ds_scan_specs", "os2ds_conversions",
                "os2ds_representations", "os2ds_matches", "os2ds_handles",
                "os2ds_metadata", "os2ds_results", "os2ds_problems"):
            self.channel.queue_declare(c,
                    passive=False, durable=True,
                    exclusive=False, auto_delete=False)
            if c != "os2ds_results":
                self.channel.basic_consume(c, message_received)

    def tearDown(self):
        self.channel.stop_consuming()
        self.connection.close()

    def test_simple_regex_match(self):
        print(Source.from_url(data_url).to_json_object())
        obj = {
            "scan_tag": "integration_test",
            "source": Source.from_url(data_url).to_json_object(),
            "rule": rule.to_json_object()
        }

        self.channel.basic_publish(exchange='',
                routing_key="os2ds_scan_specs",
                body=dumps(obj).encode())

        messages = {}
        def result_received(a, b, c, d):
            body = loads(d.decode("utf-8"))
            messages[body["origin"]] = body
            if len(messages) == 2:
                raise StopHandling()

        self.channel.basic_consume("os2ds_results", result_received)

        try:
            self.channel.start_consuming()
        except StopHandling as e:
            self.assertTrue(
                    messages["os2ds_matches"]["matched"],
                    "RegexRule match failed")
            self.assertEqual(
                    messages["os2ds_matches"]["matches"],
                    expected_matches,
                    "RegexRule match did not produce expected result")
