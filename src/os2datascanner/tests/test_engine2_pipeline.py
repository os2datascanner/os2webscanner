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
