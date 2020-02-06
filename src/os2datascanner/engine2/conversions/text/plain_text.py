from ...rules.types import InputType
from ..registry import conversion


@conversion(InputType.Text, "text/plain")
def plain_text_processor(r, **kwargs):
    with r.make_stream() as t:
        try:
            return t.read().decode()
        except UnicodeDecodeError:
            return None
