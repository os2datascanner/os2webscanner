from django.test import TestCase

from os2datascanner.projects.admin.adminapp.utils import get_codec_and_string

class UnicodeTest(TestCase):
    """Unit-tests for Unicode Dammit"""


    def test_get_codec_and_string(self):
        mybytes = "ÆØÅ#¤%&".encode("utf-16")
        encoding, mystring = get_codec_and_string(mybytes)
        self.assertEqual(get_codec_and_string(mybytes), ("UTF-16", "ÆØÅ#¤%&"))
        mybytes = "ÆØÅ#¤%&"
        self.assertEqual(get_codec_and_string(mybytes), (None, "ÆØÅ#¤%&"))

