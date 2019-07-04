import unittest
import os

from os2datascanner.engine.utils import run_django_setup

TESTDIR=os.path.dirname(__file__)

run_django_setup()

from .tests import create_webscan

class MockUrlObj:
    url="test-flydata.xml"
    scan = create_webscan()

from os2datascanner.engine.scanners.processors.xml import XmlProcessor

@unittest.skip("broken")
class ProcessorTest(unittest.TestCase):

    def testxml(self):
        with open(os.path.join(TESTDIR,'data','xml','test-flydata.xml'), encoding="utf-8") as tf:
            data = tf.read()
            parsed=XmlProcessor().process(data, MockUrlObj())
            self.assertIsNot(parsed, True)
            self.assertEqual(parsed[1],'{"Sager": {"Sag": {"@Cpr": "XXXXXX-XXXX", "Regnskab": {"CPR_x0020_nr": "XXXXXXXXXX", "Bogf\\u00f8ringsdato": "2005-06-16T00:00:00.0000000+02:00", "Bilagsnr": "20529448", "Bilagstype": "Faktura", "Bel\\u00f8b": "1524", "Beskrivelse": "Fleksydelsesbidrag"}}}}')
