import unittest
import os
TESTDIR=os.path.dirname(__file__)

import sys
import testparsetotextmock as testmock

sys.modules["django.conf"]=testmock
sys.modules["scanner.scanner.scanner"]=testmock
sys.modules["scanner.processors.processor"]=testmock
sys.modules["scanner.processors.text"]=testmock
sys.modules["os2webscanner.models.match_model"]=testmock
sys.modules["os2webscanner.models.sensitivity_level"]=testmock

class MockUrlObj:
    url="test-flydata.xml"

from scanner.processors.xml import XmlProcessor

class ProcessorTest(unittest.TestCase):

    def testxml(self):
        with open(os.path.join(TESTDIR,'data','xml','test-flydata.xml'), encoding="utf-8") as tf:
            data = tf.read()
            parsed=XmlProcessor().process(data, MockUrlObj())
            self.assertEqual(parsed[1],'{"Sager": {"Sag": {"@Cpr": "XXXXXX-XXXX", "Regnskab": {"CPR_x0020_nr": "XXXXXXXXXX", "Bogf\\u00f8ringsdato": "2005-06-16T00:00:00.0000000+02:00", "Bilagsnr": "20529448", "Bilagstype": "Faktura", "Bel\\u00f8b": "1524", "Beskrivelse": "Fleksydelsesbidrag"}}}}')
