import io
import logging
import shutil
import tempfile
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

import click

from fodt.constants import ClickOptions
from fodt.exceptions import HandlerDoneException
from fodt.xml_helpers import XMLHelper

class FontHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        self.in_section = False
        self.in_font_face = False
        self.content = io.StringIO()

    def characters(self, content: str):
        if self.in_font_face:
            return  # we remove the interior of a font-face tag
        self.content.write(xml.sax.saxutils.escape(content))

    def endElement(self, name: str):
        if name == 'office:font-face-decls':
            self.in_section = False
        elif name == 'style:font-face':
            self.in_font_face = False
        else:
            if self.in_font_face:
                return  # we remove the interior of a font-face tag
        self.content.write(XMLHelper.endtag(name))

    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if name == 'office:font-face-decls':
            self.in_section = True
        elif self.in_section:
            if name == 'style:font-face':
                self.in_font_face = True
            elif self.in_font_face:
                return  # we remove the interior of a font-face tag
        self.content.write(XMLHelper.starttag(name, attrs))


class RemoveFontData:
    def __init__(self, maindir, filename: str) -> None:
        self.maindir = maindir
        self.filename = Path(maindir) / filename

    def remove(self) -> None:
        logging.info(f"Removing binary font data from {self.filename}.")
        parser = xml.sax.make_parser()
        handler = FontHandler()
        parser.setContentHandler(handler)
        try:
            parser.parse(self.filename)
        except HandlerDoneException as e:
            pass
        tempfile_ = tempfile.mktemp()
        shutil.copy(self.filename, tempfile_)
        logging.info(f"Created backup of {self.filename} in {tempfile_}.")
        with open(self.filename, "w", encoding='utf8') as f:
            f.write(handler.content.getvalue())
        logging.info(f"Wrote updated file to {self.filename}.")
        logging.info(f"Done removing font data.")



# fodt-remove-fonts
# -----------------
# SHELL USAGE:
#   fodt-remove-fonts --filename=<file.fodt>
#
# DESCRIPTION:
#   Removes binary font data from font face declaration in file.fodt. The original
#   file is backed up to a temp file before the font data is removed.
#
# EXAMPLE:
#
#   fodt-remove-fonts --filename=main.fodt
#
@click.command()
@ClickOptions.maindir(required=False)
@click.option('--filename', required=True, help='Name of input file')
def remove_fonts(maindir: str, filename: str) -> None:
    """Removes binary font data from <filename>."""
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Removing binary font data from {filename}.")
    remover = RemoveFontData(maindir, filename)
    remover.remove()

if __name__ == "__main__":
    remove_fonts()