import json

from django.test import TestCase

from .utils import hash_handle
from .management.commands.pipeline_collector import manipulate_result

class PipelineCollectorTest(TestCase):

    def test_hash_handle(self):
        """
        Test for utils.hash_handle function.
        The test tests that the return value from the
        hash_handle function always is the same for the same
        json object. No matter how the string version of json object
        is formattet, as long as the json object is the same.
        """
        # handle1 - dummy json
        handle1 = '{"handle": {"abc": "Mdr-tl-frvgt-rb", "qpd": "xxtg", "wnm": ' \
                 '{"kkk": "shared_folder", "qqpd": "xxtg", "jjj": null, ' \
                  '"cmn": null, "ppli": null, "dsr": null}}, "rgn": "sdsm", ' \
                  '"mtd": {"pdfr": "hn", ' \
                  '"fwn": "6009036913111988543-1616249304-1001", "wnr": 1013}, ' \
                  '"scn": "2019-11-28T14:56:58"}'

        # handle2 is the json string as handle1, just without whitespaces.
        handle2 = '{"handle":{"abc":"Mdr-tl-frvgt-rb","qpd":"xxtg","wnm":' \
                  '{"kkk":"shared_folder","qqpd":"xxtg","jjj":null,"cmn":null,' \
                  '"ppli":null,"dsr":null}},"rgn":"sdsm","mtd":{"pdfr":"hn",' \
                  '"fwn":"6009036913111988543-1616249304-1001","wnr":1013},' \
                  '"scn":"2019-11-28T14:56:58"}'

        # Compare created hex value with expected hex value
        self.assertEqual(hash_handle(handle=json.loads(handle1)),
                         '8361e72900aabd95f8dd99a1d068e4b06091078662e3c5ee4c0385'
                         '3725cf21c8a21dc4e397fd78a579cc6430e68d7d3e11568e684747'
                         '491003a9a9697a505b72')
        # Compare hex value from handle1 with hex value from handle2
        self.assertEqual(hash_handle(handle=json.loads(handle1)),
                         hash_handle(handle=json.loads(handle2)))

    def test_manipulate_result(self):
        data = manipulate_result(True, { 'hejsa': 'mere hejsa' })
        print(data)