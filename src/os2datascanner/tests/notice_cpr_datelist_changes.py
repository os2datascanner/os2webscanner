import lxml.html
import datetime # noqa
import requests
import unittest

from os2datascanner.engine2.rules import cpr


class CPRTest(unittest.TestCase):
    def test_is_exception_dates_up_to_date(self):
        """
        Compare our list of exception dates to the official list from the
        CPR Office.
        """
        def parsedate(s: str) -> datetime.date:
            """
            Quick-and-dirty parser for strings such as "1. januar 1991"
            """
            danish_months = (
                "januar", "februar", "marts", "april", "maj", "juni",
                "juli", "august", "september", "oktober", "november",
                "december",
            )

            day, month, year = s.strip().replace(".", "").split()

            return datetime.date(
                int(year),
                danish_months.index(month) + 1,
                int(day)
            )

        r = requests.get(
            "https://cpr.dk/cpr-systemet/"
            "personnumre-uden-kontrolciffer-modulus-11-kontrol/"
        )

        r.raise_for_status()

        doc = lxml.html.document_fromstring(r.text)

        dates = {
            parsedate(cell.text_content())
            for cell in doc.findall('*//*[@class="web-page"]//td')
            if cell.text.strip()
        }

        self.assertEquals(dates, cpr.cpr_exception_dates)
