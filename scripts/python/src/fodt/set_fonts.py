import io
import logging
import click

from pathlib import Path
from fodt.constants import ClickOptions, Directories, TagEvent
from fodt import helpers, xml_helpers
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

class ItemHandler(xml.sax.handler.ContentHandler):
    def __init__(self, savename: str, font_decl_file: str) -> None:
        self.savename = savename
        self.font_decl_file = font_decl_file
        self.content = io.StringIO()
        self.in_section = False
        self.font_tag_name = "office:font-face-decls"

    def endDocument(self) -> None:
        self.write_file()

    def insert_font_decls(self) -> None:
        with open(self.font_decl_file, "r", encoding='utf-8') as f:
            self.content.write(f.read())

    def startDocument(self):
        self.write_xml_header()

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if name == self.font_tag_name:
            self.in_section = True
            self.insert_font_decls()
        if not self.in_section:
            self.content.write(xml_helpers.starttag(name, attrs))

    def endElement(self, name: str):
        if not self.in_section:
            self.content.write(xml_helpers.endtag(name))
        if name == self.font_tag_name:
            self.in_section = False

    def characters(self, content: str):
        if not self.in_section:
            self.content.write(xml_helpers.escape(content))

    def write_file(self):
        with open(self.savename, "w", encoding='utf-8') as f:
            f.write(self.content.getvalue())

    def write_xml_header(self) -> None:
        self.content.write(xml_helpers.HEADER)

class ReplaceFontDecls():
    def __init__(self, filename: str, savename: str, font_decl_file: str) -> None:
        logging.info(f"Replacing font-decls in {filename} and saving to {savename}.")
        parser = xml.sax.make_parser()
        handler = ItemHandler(savename, font_decl_file)
        parser.setContentHandler(handler)
        parser.parse(filename)
        logging.info(f"Done. Saved {savename}.")


# fodt-replace-fontdecls
# ----------------------
# SHELL USAGE:
#   fodt-replace-font-decls --filename=<fodt-original-file> \
#                           --savename=<fodt-new-file> \
#                           --font-decl-file=<new-font-decls>
# DESCRIPTION:
#
# Replaces the font declarations in a fodt file with the font declarations in
# the file <font-decl-file>.
#
@click.command()
@ClickOptions.filename
@click.option('--savename', type=str, required=True, help='Name of the new fodt file.')
@click.option('--font-decl-file', type=str, required=True,
               help='Name of the file containing the new font declarations.')
def set_font_decls(filename: str, savename: int, font_decl_file: str) -> None:
    logging.basicConfig(level=logging.INFO)
    replacer = ReplaceFontDecls(filename, savename, font_decl_file)

if __name__ == "__main__":
    set_font_decls()
