from bs4 import BeautifulSoup

from ...rules.types import InputType
from ..registry import conversion


@conversion(InputType.Text, "text/html")
def html_processor(r, **kwargs):
    with r.make_stream() as fp:
        return BeautifulSoup(fp, "lxml").get_text()
