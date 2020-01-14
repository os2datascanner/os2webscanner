#!/usr/bin/env python3

import os
from codecs import lookup as lookup_codec
from PyPDF2 import PdfFileReader
import olefile
from zipfile import ZipFile, BadZipFile
import mimetypes
from defusedxml.ElementTree import parse
import subprocess

guess_mime_type = lambda t: mimetypes.guess_type(t, strict=False)[0]

def _get_cifs_security_descriptor(path):
    """Attempts to parse the output of the getcifsacl command, returning a
    dictionary (unless the REVISION and CONTROL fields of the output are both
    "0x0", or the program returns an error status, in which case None is
    returned)."""
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
        if not (_check_dictionary_field(rv, "REVISION", "0x0") and
                _check_dictionary_field(rv, "CONTROL", "0x0")):
            return rv
        else:
            return None
    else:
        return None

def _codepage_to_codec(cp):
    """Retrieves the Python text codec corresponding to the given Windows
    codepage."""

    # In principle, this isn't hard: Python has lots of inbuilt codecs with
    # predictable names ("cp" followed by the string representation of the
    # codepage number), but...
    try:
        # ... codepage 65001 is an interesting special case: it's "whatever
        # WideCharToMultiByte returns when you ask it for UTF-8" (which is,
        # at least in some versions of Windows, known not to be proper UTF-8).
        # As a result, Python can only expose it as a codec on Windows! For
        # now, we treat it as normal UTF-8...
        if cp == 65001:
            return lookup_codec("utf-8")
        else:
            # All codepages must be represented with at least three digits:
            # this is only a problem for "cp037", but we may as well keep
            # things general
            return lookup_codec("cp{:03}".format(cp))
    except LookupError:
        return None

def _get_ole_metadata(fp):
    try:
        raw = olefile.OleFileIO(fp).get_metadata()

        tidied = {}
        # The value we get here is a signed 16-bit quantity, even though
        # the file format specifies values up to 65001
        tidied["codepage"] = raw.codepage
        if tidied["codepage"] < 0:
            tidied["codepage"] += 65536
        codec = _codepage_to_codec(tidied["codepage"])
        if codec:
            for name in olefile.OleMetadata.SUMMARY_ATTRIBS:
                if name in tidied:
                    continue
                value = getattr(raw, name)
                if isinstance(value, bytes):
                    value, _ = codec.decode(value)
                tidied[name] = value
        return tidied
    except FileNotFoundError:
        return None

def _process_zip_resource(fp, member, func):
    try:
        with ZipFile(fp, "r") as z:
            with z.open(member, "r") as f:
                return func(f)
    except (KeyError, BadZipFile, FileNotFoundError):
        return None

def _get_pdf_document_info(fp):
    try:
        pdf = PdfFileReader(fp)
        if pdf.getIsEncrypted():
            # Some PDFs are "encrypted" with an empty password: give that a
            # shot...
            if not pdf.decrypt(""):
                return None
        return pdf.getDocumentInfo()
    except FileNotFoundError:
        return None

def _check_dictionary_field(d, k, value=None):
    """Many of the metadata extraction functions in this file return dictionary
    or dictionary-like objects on success and None on failure -- and, depending
    on the precise structure of the underlying metadata, these objects may or
    may not contain any particular named fields.

    This utility function provides a simple way of checking for the presence of
    fields in these return values without explicitly having to check for None
    values at any point."""
    return d and k in d and d[k] is not None and (not value or value == d[k])

def type_is_ole(mime):
    return mime in ("application/msword", "application/vnd.ms-excel",
            "application/vnd.ms-powerpoint")

def type_is_pdf(mime):
    return mime in ("application/pdf", "application/x-pdf",
            "application/x-bzpdf", "application/x-gzpdf")

def type_is_ooxml(mime):
    return mime.startswith("application/vnd.openxmlformats-officedocument.")

def type_is_opendocument(mime):
    return mime.startswith("application/vnd.oasis.opendocument.")

def guess_responsible_party(path):
    """Returns a dictionary of labelled speculations about the person
    responsible for the path @path.

    These labels are highly likely to indicate the person responsible for the
    path, but are ambiguous and must be compared against other organisational
    data:

    * "od-modifier", the plaintext name of the last person to modify an
      OpenDocument document
    * "ooxml-modifier", the plaintext name of the last person to modify an
      Office Open XML document
    * "ole-modifier", the plaintext name of the last person to modify an OLE-
      based Microsoft Office document (.doc, .ppt, .xls, etc.)

    These labels are both ambiguous and less likely to indicate the person
    responsible for the path, but can be compared with other data to increase
    the confidence of the guess:

    * "od-creator", the plaintext name of the person who initially created an
      OpenDocument document
    * "ooxml-creator", the plaintext name of the person who initially created
      an Office Open XML document
    * "ole-creator", the plaintext name of the person who initially created an
      OLE-based Microsoft Office document
    * "pdf-author", the plaintext author name given in a PDF document's
      metadata

    These labels refer unambiguously to an individual person, but are less
    likely to indicate the person responsible for the file's content:

    * "filesystem-owner-sid", the SID of the owner of a CIFS filesystem object
    * "filesystem-owner-uid", the UID of the owner of a Unix filesystem object"""
    speculations = {}

    # File metadata-based speculations
    mime = guess_mime_type(path)
    if mime:
        if type_is_opendocument(mime):
            f = None
            with open(path, "rb") as fp:
                f = _process_zip_resource(fp, "meta.xml", parse)
            if f:
                content = f.find("{urn:oasis:names:tc:opendocument:xmlns:office:1.0}meta")
                if content:
                    lm = content.find("{http://purl.org/dc/elements/1.1/}creator")
                    if lm is not None and lm.text:
                        speculations["od-modifier"] = lm.text.strip()
                    c = content.find("{urn:oasis:names:tc:opendocument:xmlns:meta:1.0}initial-creator")
                    if c is not None and c.text:
                        speculations["od-creator"] = c.text.strip()
        elif type_is_ooxml(mime):
            f = None
            with open(path, "rb") as fp:
                f = _process_zip_resource(fp, "docProps/core.xml", parse)
            if f:
                lm = f.find("{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}lastModifiedBy")
                if lm is not None and lm.text:
                    speculations["ooxml-modifier"] = lm.text.strip()
                c = f.find("{http://purl.org/dc/elements/1.1/}creator")
                if c is not None and c.text:
                    speculations["ooxml-creator"] = c.text.strip()
        elif type_is_ole(mime):
            m = None
            with open(path, "rb") as fp:
                m = _get_ole_metadata(fp)
            if m:
                if "last_saved_by" in m:
                    speculations["ole-modifier"] = m["last_saved_by"]
                if "author" in m:
                    speculations["ole-creator"] = m["author"]
        elif type_is_pdf(mime):
            doc_info = None
            with open(path, "rb") as fp:
                doc_info = _get_pdf_document_info(fp)
            if _check_dictionary_field(doc_info, "/Author"):
                speculations["pdf-author"] = doc_info["/Author"]

    # Filesystem-based speculations
    cifs_acl = _get_cifs_security_descriptor(path)
    if _check_dictionary_field(cifs_acl, "OWNER"):
        speculations["filesystem-owner-sid"] = cifs_acl["OWNER"]
    # stat will always work unless the path is invalid
    try:
        stat = os.stat(path)
        speculations["filesystem-owner-uid"] = stat.st_uid
    except FileNotFoundError:
        pass

    return speculations
