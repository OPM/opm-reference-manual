import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions
from fodt.xml_handlers import PassThroughFilterHandler


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
        handler = PassThroughFilterHandler()
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
