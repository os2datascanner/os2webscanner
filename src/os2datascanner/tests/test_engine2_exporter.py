import unittest

from os2datascanner.engine2.pipeline.exporter import filter_message
from os2datascanner.utils.system_utilities import json_utf8_decode

class Engine2TestExporter(unittest.TestCase):

    def test_metadata_filter(self):
        metadata_example = b'{"scan_tag":"2019-11-28T14:56:58","handle":{"type":"smbc","source":{"type":"smbc","unc":"//172.16.20.172/webscanner_shared_folder","user":"magenta","password":"secret","domain":"","driveletter":null},"path":"subdir1/Notworks-Copy(2)/hej.dk/Midler-til-frivilligt-arbejde.pdf"},"metadata":{"pdf-author":"hn32","filesystem-owner-uid":1000,"filesystem-owner-sid":"S-1-5-21-2600903691-3111988543-1616249304-1001"}}'
        metadata_example_success = "{'scan_tag': '2019-11-28T14:56:58', 'handle': {'type': 'smbc', 'source': {'type': 'smbc', 'unc': '//172.16.20.172/webscanner_shared_folder', 'domain': '', 'driveletter': None}, 'path': 'subdir1/Notworks-Copy(2)/hej.dk/Midler-til-frivilligt-arbejde.pdf'}, 'metadata': {'pdf-author': 'hn32', 'filesystem-owner-uid': 1000, 'filesystem-owner-sid': 'S-1-5-21-2600903691-3111988543-1616249304-1001'}}"

        self.assertEqual(str(filter_message(json_utf8_decode(metadata_example))),
                         str(metadata_example_success))

    def test_problem_filter(self):
        problem_example = b'{"where":{"type":"zip","handle":{"type":"zip","source":{"type":"zip","handle":{"type":"smbc","source":{"type":"smbc","unc":"//172.16.20.172/webscanner_shared_folder","user":"magenta","password":"secret","domain":"","driveletter":null},"path":"hej.dk/3.zip"}},"path":"3/TR.xlsx"}},"problem":"unavailable","extra":["\/\/\/\/172.16.20.172\/\/webscanner_shared_folder\/\/hej.dk\/\/3.zip","(13,\'Permissiondenied\')"]}'
        problem_example_success = "{'where': {'type': 'zip', 'handle': {'type': 'zip', 'source': {'type': 'zip', 'handle': {'type': 'smbc', 'source': {'type': 'smbc', 'unc': '//172.16.20.172/webscanner_shared_folder', 'domain': '', 'driveletter': None}, 'path': 'hej.dk/3.zip'}}, 'path': '3/TR.xlsx'}}, 'problem': 'unavailable', 'extra': ['////172.16.20.172//webscanner_shared_folder//hej.dk//3.zip', \"(13,'Permissiondenied')\"]}"

        self.assertEqual(str(filter_message(json_utf8_decode(problem_example))),
                         str(problem_example_success))

    def test_match_filter(self):
        match_example = b'{"scan_spec":{"scan_tag":"2019-11-28T14:56:58","source":{"type":"smbc","unc":"//172.16.20.172/webscanner_shared_folder","user":"magenta","password":"secret","domain":"","driveletter":null},"rule":{"type":"cpr","modulus_11":false,"ignore_irrelevant":false},"configuration":{}},"handle":{"type":"smbc","source":{"type":"smbc","unc":"//172.16.20.172/webscanner_shared_folder","user":"magenta","password":"secret","domain":"","driveletter":null},"path":"subdir1/Notworks-Copy(2)/innocent_cat_version3.jpg"},"matched":true,"matches":[{"rule":{"type":"cpr","modulus_11":false,"ignore_irrelevant":false},"matches":[{"offset":0,"match":"0104XXXXXX","context":"XXXXXX-XXXX","context_offset":0}]}]}'
        match_example_success = "{'scan_spec': {'scan_tag': '2019-11-28T14:56:58', 'source': {'type': 'smbc', 'unc': '//172.16.20.172/webscanner_shared_folder', 'domain': '', 'driveletter': None}, 'rule': {'type': 'cpr', 'modulus_11': False, 'ignore_irrelevant': False}, 'configuration': {}}, 'handle': {'type': 'smbc', 'source': {'type': 'smbc', 'unc': '//172.16.20.172/webscanner_shared_folder', 'domain': '', 'driveletter': None}, 'path': 'subdir1/Notworks-Copy(2)/innocent_cat_version3.jpg'}, 'matched': True, 'matches': [{'rule': {'type': 'cpr', 'modulus_11': False, 'ignore_irrelevant': False}, 'matches': [{'offset': 0, 'match': '0104XXXXXX', 'context': 'XXXXXX-XXXX', 'context_offset': 0}]}]}"

        self.assertEqual(str(filter_message(json_utf8_decode(match_example))),
                         str(match_example_success))