from os import listdir
from tempfile import TemporaryDirectory
from subprocess import run, PIPE

from ..core import (Handle,
        Source, Resource, SourceManager, ResourceUnavailableError)
from ..file import FilesystemResource
from .derived import DerivedSource


def libreoffice(*args):
    """Invokes LibreOffice with a fresh settings directory (which will be
    deleted as soon as the program finishes) and returns a CompletedProcess
    with both stdout and stderr captured."""
    with TemporaryDirectory() as settings:
        return run(
                ["libreoffice",
                        "-env:UserInstallation=file://{0}".format(settings),
                        *args], stdout=PIPE, stderr=PIPE)


@Source.mime_handler(
        "application/msword",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",

        "application/vnd.ms-excel",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
class LibreOfficeSource(DerivedSource):
    type_label = "lo"

    def _generate_state(self, sm):
        with SourceManager(sm) as derived:
            resource = self.handle.follow(derived)
            mime_type = resource.compute_type()
            with self.handle.follow(derived).make_path() as p:
                with TemporaryDirectory() as outputdir:
                    result = libreoffice(
                            "--convert-to", "html",
                            "--outdir", outputdir, p)
                    if result.returncode == 0:
                        yield outputdir
                    else:
                        raise ResourceUnavailableError(self.handle,
                                "LibreOffice exited abnormally",
                                result.returncode)

    def handles(self, sm):
        for name in listdir(sm.open(self)):
            yield LibreOfficeObjectHandle(self, name)


@Handle.stock_json_handler("lo-object")
class LibreOfficeObjectHandle(Handle):
    type_label = "lo-object"
    resource_type = FilesystemResource

    @property
    def presentation(self):
        return "{0} (in {1})".format(self.relative_path, self.source.handle)

    def censor(self):
        return LibreOfficeObjectHandle(
                self.source._censor(), self.relative_path)
