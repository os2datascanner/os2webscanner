from .types import OutputType
from .registry import conversion


@conversion(OutputType.Fallback)
def fallback_processor(r, **kwargs):
    return True
