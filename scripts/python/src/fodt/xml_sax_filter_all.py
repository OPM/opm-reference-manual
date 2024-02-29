import io
import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions
from fodt.xml_helpers import XMLHelper

class ElementHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        self.content = io.StringIO()
        self.start_tag_open = False  # For empty tags, do not close with />

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(XMLHelper.escape(content))

    def endElement(self, name: str):
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class FilterAll:
    def __init__(self, maindir: str) -> None:
        self.maindir = Path(maindir)

    def run_filter(self) -> None:
        for i, filename in enumerate(self.maindir.rglob("*.fodt"), start=1):
            logging.info(f"Processing file: {filename}")
            self.filter_file(filename)
            #if i == 1:
            #    break

    def filter_file(self, filename: Path) -> None:
        parser = xml.sax.make_parser()
        handler = ElementHandler()
        parser.setContentHandler(handler)
        parser.parse(filename)
        with open(filename, "w", encoding='utf8') as f:
            f.write(handler.get_content())



# USAGE:
#
#   fodt-xml-sax-filter-all \
#        --maindir=<main directory> \
#
# DESCRIPTION:
#
#  Runs xml.sax filter on all .fodt files in the main directory. This means that
#  each .fodt file is read by the xml.sax parser, and the content is then written back
#  to the file using xml.sax.saxutils.escape() to escape the content.
#  This is useful to check for inconsistencies in the XML content written by LibreOffice
#  and the content written by the xml.sax parser and to initially algin the XML content
#  with the format written by LibreOffice.
#
@click.command()
@ClickOptions.maindir(required=False)
def xml_sax_filter_all(maindir: str) -> None:
    """Filter all .fodt files in maindir."""
    logging.basicConfig(level=logging.INFO)
    FilterAll(maindir).run_filter()
