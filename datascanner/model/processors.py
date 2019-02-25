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

processors = {
    "text/plain": plain_text_processor,
    "image/png": image_processor,
    "application/pdf": pdf_processor,
    "text/html": html_processor
}
