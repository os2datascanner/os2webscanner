from django import template

from os2datascanner.engine2.model.core import Handle


register = template.Library()


@register.filter
def present(handle):
    """Returns the presentation of the given Handle."""
    if isinstance(handle, Handle):
        return handle.presentation
    else:
        return None


@register.filter
def present_url(handle):
    """Returns the presentation URL of the given Handle (or, if it doesn't
    define one, of its first parent that does)."""
    if isinstance(handle, Handle):
        while not handle.presentation_url and handle.source.handle:
            handle = handle.source.handle
        return handle.presentation_url
    else:
        return None


@register.filter
def find_parent(handle, type_label):
    """If the given Handle's type label matches the argument, then returns it;
    otherwise, returns the first parent Handle with that appropriate type label
    (or None if there wasn't one)."""
    if isinstance(handle, Handle):
        while handle and handle.type_label != type_label:
            handle = handle.source.handle
        return handle
    else:
        return None
