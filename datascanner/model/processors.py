#!/usr/bin/env python3

from subprocess import run, PIPE, DEVNULL

def plain_text_processor(r, **kwargs):
    with r.make_stream() as t:
        try:
            return t.read().decode()
        except UnicodeDecodeError:
            return None

def image_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["tesseract", f, "stdout"],
                universal_newlines=True,
                stdout=PIPE,
                stderr=DEVNULL, **kwargs).stdout.strip()

def pdf_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["pdftotext", f, "-"],
                universal_newlines=True,
                stdout=PIPE,
                stderr=DEVNULL, **kwargs).stdout.strip()

def html_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["html2text", f],
                universal_newlines=True,
                stdout=PIPE,
                stderr=DEVNULL, **kwargs).stdout.strip()

def libreoffice_txt_processor(r, **kwargs):
    with r.make_path() as f:
        return run(["unoconv", "--stdout", "-v", "-v", "-v", "--format", "txt", f],
                universal_newlines=True,
                stdout=PIPE,
                stderr=sys.stderr, **kwargs).stdout.strip()

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
