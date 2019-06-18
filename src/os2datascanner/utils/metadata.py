#!/usr/bin/env python3

import os
from PyPDF2 import PdfFileReader
import olefile
from zipfile import ZipFile, BadZipFile
import mimetypes
from defusedxml.ElementTree import parse
import subprocess

guess_mime_type = lambda t: mimetypes.guess_type(t, strict=False)[0]

def _get_cifs_security_descriptor(path):
    """\
Attempts to parse the output of the getcifsacl command, returning a dictionary
(unless the REVISION and CONTROL fields of the output are both "0x0", or the
program returns an error status, in which case None is returned)."""
    r = subprocess.run(["getcifsacl", path],
            stdout=subprocess.PIPE, universal_newlines=True)
    if r.returncode == 0:
        rv = {}
        for line in r.stdout.splitlines():
            k, v = [f.strip() for f in line.split(":", maxsplit=1)]
            if k in rv:
                if not isinstance(rv[k], list):
                    rv[k] = [rv[k]]
                rv[k].append(v)
            else:
                rv[k] = v
        if not (_quadruple_check(rv, "REVISION", "0x0") and
                _quadruple_check(rv, "CONTROL", "0x0")):
            return rv
        else:
            return None
    else:
        return None

def _get_ole_metadata(path):
    try:
        with open(path, "rb") as f:
            m = olefile.OleFileIO(f).get_metadata()
            for v in olefile.OleMetadata.SUMMARY_ATTRIBS:
                print(v, getattr(m, v))
            return m
    except:
        raise

def _process_zip_resource(path, member, func):
    try:
        with ZipFile(path, "r") as z:
            with z.open(member, "r") as f:
                return func(f)
    except (KeyError, BadZipFile):
        return None

def _get_pdf_document_info(path):
    with open(path, "rb") as f:
        return PdfFileReader(f).getDocumentInfo()

def _quadruple_check(d, k, value=None):
    """
Returns true if and only if @d is a dictionary which has a non-None associated
value for @k (and, if @value is not None, that it's equal to the associated
value).
"""
    return d and k in d and d[k] is not None and (d[k] == value or not value)

def guess_responsible_party(path):
    """\
Returns an unordered list of labelled speculations about the person responsible
for the path @path.

These labels are highly likely to indicate the person responsible for the path,
but are ambiguous and must be compared against other organisational data:

* "libreoffice-last-modified-by", the plaintext name of the last person to
  modify a LibreOffice document
* "ooxml-last-modified-by", the plaintext name of the last person to modify an
  Office Open XML document
* "ole-last-modified-by", the plaintext name of the last person to modify an
  OLE-based Microsoft Office document (.doc, .ppt, .xls, etc.)

These labels are both ambiguous and less likely to indicate the person
responsible for the path, but can be compared with other data to increase the
confidence of the guess:

* "libreoffice-creator", the plaintext name of the person who initially created
  a LibreOffice document
* "ooxml-creator", the plaintext name of the person who initially created an
  Office Open XML document
* "ole-creator", the plaintext name of the person who initially created an OLE-
  based Microsoft Office document
* "pdf-author", the plaintext author name given in a PDF document's metadata

These labels refer unambiguously to an individual person, but are less likely
to indicate the person responsible for the file's content:

* "filesystem-owner-sid", the SID of the owner of a CIFS filesystem object
* "filesystem-owner-uid", the UID of the owner of a Unix filesystem object"""
    speculations = []

    # File metadata-based speculations
    mime = guess_mime_type(path)
    if mime:
        if mime.startswith("application/vnd.oasis.opendocument."):
            f = _process_zip_resource(path, "meta.xml", parse)
            if f:
                content = f.find("{urn:oasis:names:tc:opendocument:xmlns:office:1.0}meta")
                if content:
                    lm = content.find("{http://purl.org/dc/elements/1.1/}creator")
                    if lm is not None:
                        speculations.append(("libreoffice-modifier", lm.text.strip()))
                    c = content.find("{urn:oasis:names:tc:opendocument:xmlns:meta:1.0}initial-creator")
                    if c is not None:
                        speculations.append(("libreoffice-creator", c.text.strip()))
        elif mime.startswith("application/vnd.openxmlformats-officedocument."):
            f = _process_zip_resource(path, "docProps/core.xml", parse)
            if f:
                lm = f.find("{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}lastModifiedBy")
                if lm is not None:
                    speculations.append(("ooxml-modifier", lm.text.strip()))
                c = f.find("{http://purl.org/dc/elements/1.1/}creator")
                if c is not None:
                    speculations.append(("ooxml-creator", c.text.strip()))
        elif mime == "application/msword" or mime == "application/vnd.ms-excel" or \
                mime == "application/vmd.ms-powerpoint":
            m = _get_ole_metadata(path)
            if m:
                # XXX: we need to understand the m.codepage field in order to
                # convert the other fields from bytes to unicode
                if m.last_saved_by:
                    speculations.append(("ole-last-modified-by", m.last_saved_by))
                if m.author:
                    speculations.append(("ole-creator", m.author))
        elif mime == "application/pdf" or mime == "application/x-pdf" or \
                mime == "application/x-bzpdf" or mime == "application/x-gzpdf":
            doc_info = _get_pdf_document_info(path)
            if _quadruple_check(doc_info, "/Author"):
                speculations.append(("pdf-author", doc_info["/Author"]))

    # Filesystem-based speculations
    cifs_acl = _get_cifs_security_descriptor(path)
    if _quadruple_check(cifs_acl, "OWNER"):
        speculations.append(("filesystem-owner-sid", cifs_acl["OWNER"]))
    # stat will always work
    stat = os.stat(path)
    speculations.append(("filesystem-owner-uid", stat.st_uid))

    return speculations

if __name__ == '__main__':
    import sys
    for i in sys.argv[1:]:
        print(guess_responsible_party(i))
