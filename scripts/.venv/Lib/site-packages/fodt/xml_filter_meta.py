import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions, Directories, FileExtensions
from fodt.xml_handlers import PassThroughFilterHandler


class FilterAll:
    def __init__(self, maindir: str) -> None:
        self.maindir = Path(maindir)

    def run_filter(self) -> None:
        meta_dir = self.maindir / Directories.meta / Directories.sections
        if not meta_dir.is_dir():
            logging.info(f"Directory {meta_dir} does not exist.")
            return
        for i, filename in enumerate(meta_dir.glob("*.xml"), start=1):
            logging.info(f"Processing file: {filename}")
            self.filter_file(filename)
            #if i == 1:
            #    break

    def filter_file(self, filename: Path) -> None:
        parser = xml.sax.make_parser()
        handler = PassThroughFilterHandler(add_header=False)
        parser.setContentHandler(handler)
        parser.parse(filename)
        with open(filename, "w", encoding='utf8') as f:
            f.write(handler.get_content())



# USAGE:
#
#   fodt-xml-sax-filter-meta \
#        --maindir=<main directory> \
#
# DESCRIPTION:
#
#    Runs xml.sax pass-through filter on all xml files in the parts/meta/sections
#  directory. The files in this directory are used by among other the
#  fodt-add-keyword script.
#    This means that each xml file is read by the xml.sax parser, and
#  the content is then written back to the file using xml.sax.saxutils.escape()
#  to escape the content.
#    This is useful to check for inconsistencies in the XML content written by LibreOffice
#  and the content written by the xml.sax parser and to initially algin the XML content
#  with the format written by LibreOffice.
#
@click.command()
@ClickOptions.maindir(required=False)
def xml_sax_filter_meta(maindir: str) -> None:
    """Filter all xml files in the meta dir."""
    logging.basicConfig(level=logging.INFO)
    FilterAll(maindir).run_filter()
