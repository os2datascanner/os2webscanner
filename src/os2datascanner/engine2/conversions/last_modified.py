from ..rules.types import InputType
from .registry import conversion


@conversion(InputType.LastModified)
def last_modified_processor(r):
    if hasattr(resource, "get_last_modified"):
        return resource.get_last_modified()
    else:
        return None
