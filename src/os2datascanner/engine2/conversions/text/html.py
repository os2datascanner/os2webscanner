from bs4 import BeautifulSoup

from ..types import OutputType
from ..registry import conversion


@conversion(OutputType.Text, "text/html")
def html_processor(r, **kwargs):
    with r.make_stream() as fp:
        return BeautifulSoup(fp, "lxml").get_text()
