#!/usr/bin/env python3

from subprocess import run, PIPE, DEVNULL

def plain_text_processor(f, **kwargs):
    try:
        with open(f, "rt") as t:
            return t.read()
    except UnicodeDecodeError:
        return None

def image_processor(f, **kwargs):
    return run(["tesseract", f, "stdout"],
            timeout=2,
            universal_newlines=True,
            stdout=PIPE,
            stderr=DEVNULL, **kwargs).stdout.strip()

def pdf_processor(f, **kwargs):
    return run(["pdftotext", f, "-"],
            timeout=2,
            universal_newlines=True,
            stdout=PIPE,
            stderr=DEVNULL, **kwargs).stdout.strip()

def html_processor(f, **kwargs):
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
