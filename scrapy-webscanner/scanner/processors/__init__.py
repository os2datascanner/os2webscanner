# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Processors for processing and converting spider and queue items."""
from .processor import Processor
from .text import TextProcessor
from .html import HTMLProcessor
from .zip import ZipProcessor
from .ocr import OCRProcessor
from .pdf import PDFProcessor
from .csv_processor import CSVProcessor
from .libreoffice import LibreOfficeProcessor
from .xml import XmlProcessor

Processor.register_processor(TextProcessor.item_type, TextProcessor)
Processor.register_processor(HTMLProcessor.item_type, HTMLProcessor)
Processor.register_processor(ZipProcessor.item_type, ZipProcessor)
Processor.register_processor(OCRProcessor.item_type, OCRProcessor)
Processor.register_processor(PDFProcessor.item_type, PDFProcessor)
Processor.register_processor(CSVProcessor.item_type, CSVProcessor)
Processor.register_processor(LibreOfficeProcessor.item_type, LibreOfficeProcessor)
Processor.register_processor(XmlProcessor.item_type, XmlProcessor)

__all__ = ["html", "libreoffice", "pdf", "ocr", "zip", "text", "csv_processor", "xml"]
