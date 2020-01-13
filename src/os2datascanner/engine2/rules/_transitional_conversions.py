from    bs4 import BeautifulSoup
import  sys
from    subprocess import run, PIPE, DEVNULL

from    .types import InputType, conversion


@conversion(InputType.Text, "text/plain")
def plain_text_processor(r, **kwargs):
    with r.make_stream() as t:
        try:
            return t.read().decode()
        except UnicodeDecodeError:
            return None


@conversion(InputType.Text, "image/png", "image/jpeg")
def image_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["tesseract", f, "stdout"],
                universal_newlines=True,
                stdout=PIPE,
                stderr=DEVNULL, **kwargs).stdout.strip()


@conversion(InputType.Text, "text/html")
def html_processor(r, **kwargs):
    with r.make_stream() as fp:
        return BeautifulSoup(fp, "lxml").get_text()
