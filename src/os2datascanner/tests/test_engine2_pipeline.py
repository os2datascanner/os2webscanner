from json import loads, dumps
import unittest
from contextlib import closing
from collections import namedtuple

import os2datascanner.engine2.model.data as e2m_data
import os2datascanner.engine2.rules.regex as e2r_regex
import os2datascanner.engine2.pipeline.explorer as e2p_explorer


class DummyChannel:
    def __init__(self):
        self._messages = []

    def basic_ack(self, delivery_tag):
        pass

    def basic_publish(self, exchange, routing_key, body):
        self._messages.append((routing_key, body))

    def _consume_message(self):
        (queue, body), self._messages = self._messages[0], self._messages[1:]
        return (queue, loads(body.decode("utf-8")))


class DummyMethod:
    delivery_tag = 12345


DummyArgs = namedtuple("DummyArgs", [
        "sources", "conversions", "representations", "matches", "handles",
        "metadata", "problems"])


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.channel = DummyChannel()

    def test_explorer_simple(self):
        e2p_explorer.args = DummyArgs(
                conversions="dummy_conversions",
                problems="dummy_problems",
                sources=None, representations=None, matches=None, handles=None,
                metadata=None)

        source = e2m_data.DataSource(b"Hello, world", "text/plain")
        with closing(source.handles(None)) as h:
            unique_handle = next(h)
        rule = e2r_regex.RegexRule("world")
        rule_j = rule.to_json_object()

        scan_spec = {
            "source": source.to_json_object(),
            "rule": rule_j,
            "scan_tag": "dummy! dummy! dummy!"
        }

        e2p_explorer.message_received(self.channel,
                DummyMethod(), None, dumps(scan_spec).encode("utf-8"))

        self.assertEqual(self.channel._consume_message(),
                ("dummy_conversions", {
                    "scan_spec": scan_spec,
                    "progress": {
                        "matches": [],
                        "rule": rule_j
                    },
                    "handle": unique_handle.to_json_object()
                }))
