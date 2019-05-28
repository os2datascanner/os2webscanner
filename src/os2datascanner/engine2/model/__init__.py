"""An experimental new model for OS2datascanner

This package contains a prototype of a new model for OS2datascanner.

At the core of this model (and therefore, funnily enough, in the model.core
module) lie three classes: Source, Handle, and Resource. A Source is something
that can generate Handles; a Handle is a named thing that points to a Resource;
and a Resource is a concrete object that can be accessed at a filesystem path
or as a Python stream.

Sources exist for many kinds of resources, like local filesystems, CIFS network
shares, and websites. But some Sources can also be constructed from Handles:
for example, if you find a Handle that references a Zip archive, you can give
that Handle to a ZipSource, which will generate Handles for the contents of the
Zip file. If you find a Zip file inside the Zip file, then you can even give
its Handle to a new ZipSource... and so on all the way down.

Everything looks the same to the model. If you have a Resource, you can find
its filesystem path, even if it doesn't actually have one -- if, say, it points
to a file inside an archive on a website, then its content will temporarily
appear on the filesystem when you ask the model for its path.
"""

# Import everything that provides a URL or MIME type handler
from . import smb # noqa
from . import tar # noqa
from . import zip # noqa
from . import data # noqa
from . import http # noqa
from . import filtered # noqa
