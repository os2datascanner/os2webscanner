from    os import getenv
from    json import dumps, loads
import  pika
import  unittest

from    os2datascanner.engine2.pipeline.utilities import json_event_processor
from    os2datascanner.engine2.model.core import Source
from    os2datascanner.engine2.rules.regex import RegexRule
from    os2datascanner.engine2.rules.logical import OrRule

from    .test_engine2_pipeline import (
        handle_message, data, data_url, rule, expected_matches)


class StopHandling(Exception):
    pass


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
                self.channel.basic_consume(c,
                        json_event_processor(handle_message))

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
