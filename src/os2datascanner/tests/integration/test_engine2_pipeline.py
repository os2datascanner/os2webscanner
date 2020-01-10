from    os import getenv
import  sys
from    json import dumps, loads
import  pika
import  base64
import  unittest
import  subprocess

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


def python(*args):
    """Starts a new instance of this Python interpreter with the specified
    arguments. Standard output and standard error will be passed through."""
    return subprocess.Popen([sys.executable, *args])


class StopHandling(Exception):
    pass


class Engine2PipelineTests(unittest.TestCase):
    def setUp(self):
        amqp_host = getenv("AMQP_HOST", "localhost")

        python("-m", "os2datascanner.engine2.pipeline._consume_queue",
                "--host", amqp_host,
                "os2ds_scan_specs", "os2ds_conversions",
                "os2ds_representations", "os2ds_matches", "os2ds_handles",
                "os2ds_metadata", "os2ds_problems", "os2ds_results").wait()
        self.explorer = python(
                "-m", "os2datascanner.engine2.pipeline.explorer",
                "--host", amqp_host)
        self.processor = python(
                "-m", "os2datascanner.engine2.pipeline.processor",
                "--host", amqp_host)
        self.matcher = python(
                "-m", "os2datascanner.engine2.pipeline.matcher",
                "--host", amqp_host)
        self.tagger = python(
                "-m", "os2datascanner.engine2.pipeline.tagger",
                "--host", amqp_host)
        self.exporter = python(
                "-m", "os2datascanner.engine2.pipeline.exporter",
                "--host", amqp_host)

        parameters = pika.ConnectionParameters(
                host=amqp_host,
                heartbeat=6000)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.channel.queue_declare("os2ds_scan_specs",
                passive=False, durable=True,
                exclusive=False, auto_delete=False)
        self.channel.queue_declare("os2ds_results",
                passive=False, durable=True,
                exclusive=False, auto_delete=False)

    def tearDown(self):
        self.channel.stop_consuming()
        self.connection.close()
        for p in (self.explorer, self.processor, self.matcher, self.tagger,
                self.exporter):
            p.kill()
            p.wait()

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
        def message_received(a, b, c, d):
            body = loads(d.decode("utf-8"))
            messages[body["origin"]] = body
            if len(messages) == 2:
                raise StopHandling()

        self.channel.basic_consume("os2ds_results", message_received)

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
