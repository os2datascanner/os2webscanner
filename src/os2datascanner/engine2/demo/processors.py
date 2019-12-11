import sys
from subprocess import run, PIPE, DEVNULL

from ..rules.types import InputType, conversion


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


@conversion(InputType.Text, "application/pdf")
def pdf_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["pdftotext", f, "-"],
                universal_newlines=True,
                stdout=PIPE,
                stderr=DEVNULL, **kwargs).stdout.strip()


@conversion(InputType.Text, "text/html")
def html_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["html2text", f],
                universal_newlines=True,
                stdout=PIPE,
                stderr=DEVNULL, **kwargs).stdout.strip()


@conversion(InputType.Text,
        "application/vnd.oasis.opendocument.text",
        "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document")
def libreoffice_txt_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["unoconv", "--stdout", "-v", "-v", "-v", "--format", "txt", f],
                universal_newlines=True,
                stdout=PIPE,
                stderr=sys.stderr, **kwargs).stdout.strip()


@conversion(InputType.Text,
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.ms-excel")
def libreoffice_csv_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["unoconv", "--stdout", "-v", "-v", "-v", "--format", "csv",
                    "--export", "FilterOptions=59,34,0,1", f],
                 universal_newlines=True,
                 stdout=PIPE,
                 stderr=DEVNULL, **kwargs).stdout.strip()


processors = {
    "text/plain": plain_text_processor,
    "image/png": image_processor,
    "image/jpeg": image_processor,
    "application/pdf": pdf_processor,
    "text/html": html_processor,
    "application/vnd.oasis.opendocument.text": libreoffice_txt_processor,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": libreoffice_txt_processor,
    "application/vnd.oasis.opendocument.spreadsheet": libreoffice_csv_processor,
    "application/vnd.ms-excel": libreoffice_csv_processor
}
