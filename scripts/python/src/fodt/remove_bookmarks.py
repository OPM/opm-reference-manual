# Remove bookmark refs from the master style section in all subdocuments.

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
    # Find the master-styles section and remove all bookmark refs from it.
    # The master-styles section has tag name "office:master-styles".
    # A book mark ref has tag name "text:bookmark-ref".

    def __init__(self) -> None:
        self.content = io.StringIO()
        self.in_master_styles = False
        self.nesting = 0
        self.start_tag_open = False

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(XMLHelper.escape(content))

    def endElement(self, name: str):
        if self.in_master_styles:
            if name == "office:master-styles":
                self.in_master_styles = False
            elif name == "text:bookmark-ref":
                # remove this tag
                return
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
        # logging.info(f"startElement: {name}")
        if (not self.in_master_styles) and name == "office:master-styles":
            self.in_master_styles = True
        if self.in_master_styles and name == "text:bookmark-ref":
            # remove this tag
            return
        if self.start_tag_open:
            self.content.write(">")
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))

class RemoveBookmarksFromMasterStyles():
    def __init__(self, maindir: str, filename: str|None, directory: str|None) -> None:
        self.maindir = Path(maindir)
        self.filename = filename
        self.directory = directory

    def remove_bookmarks(self) -> None:
        if self.directory is not None:
            filenames = list(Path(self.maindir / self.directory).glob("*.fodt"))
        else:
            filenames = [Path(self.maindir / self.filename)]
        logging.info(f"Found {len(filenames)} files.")
        logging.info(f"Filenames: {filenames}")
        for filename in filenames:
            self.remove_bookmarks_from_file(filename)

    def remove_bookmarks_from_file(self, filename: str) -> None:
        logging.info(f"Processing {filename}.")
        parser = xml.sax.make_parser()
        handler = ElementHandler()
        parser.setContentHandler(handler)
        parser.parse(filename)
        with open(filename, "w", encoding='utf8') as f:
            f.write(handler.get_content())


# USAGE:
#
#   fodt-remove-bookmarks-from-master-styles \
#        --filename=<fodt_input_file>
#        --directory=<subdocument directory>
#
# DESCRIPTION:
#
#   Remove bookmark refs from the master style section in all subdocuments in the
#   specified directory or in the specified file. Filenames and directory names
#   are relative to the main directory.
#
@click.command()
@ClickOptions.maindir(required=False)
@click.option(
    "--filename",
    help="Subdocument filename.",
    required=False,
)
@click.option(
    "--directory",
    help="Subdocument directory.",
    required=False,
)
def remove_bookmarks_from_master_styles(
    maindir: str, filename: str|None, directory: str|None
) -> None:
    """Remove bookmark refs from the master style section in all subdocuments."""
    logging.basicConfig(level=logging.INFO)
    if (filename is not None) and (directory is not None):
        raise ValueError("Specify either filename or directory.")
    if filename is None and directory is None:
        raise ValueError("Specify either filename or directory.")
    logging.info(f"Removing bookmark refs from master styles in {maindir}.")
    RemoveBookmarksFromMasterStyles(maindir, filename, directory).remove_bookmarks()

if __name__ == "__main__":
    remove_bookmarks_from_master_styles()
