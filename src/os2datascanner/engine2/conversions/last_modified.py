from .types import OutputType
from .registry import conversion


@conversion(OutputType.LastModified)
def last_modified_processor(resource):
    if hasattr(resource, "get_last_modified"):
        return resource.get_last_modified()
    else:
        return None
