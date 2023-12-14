# Change the status of a keyword in Appendix A.
# This is done by change the color code in the status column.
# Two colors are used: green and and orange.
# - Green means that the keyword is fully implemented.
# - Orange means that the keyword is available but not fully implemented.

import io
import logging
import shutil
import re
import tempfile
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions, Directories, FileExtensions, KeywordStatus
from fodt.xml_helpers import XMLHelper

class AppendixStatusColorHandler(xml.sax.handler.ContentHandler):
    def __init__(self, keyword: str, status: KeywordStatus) -> None:
        self.keyword = keyword
        self.status = status
        self.in_section = False
        self.in_table_row = False
        self.in_table_cell = False
        self.current_tag_name = None
        self.content = io.StringIO()
        self.current_keyword = None
        self.keyword_found = False

    def characters(self, content: str):
        self.content.write(xml.sax.saxutils.escape(content))

    def endElement(self, name: str):
        if not self.keyword_found:
            if name == "table:table-row":
                self.in_table_row = False
            elif self.in_table_row and name == "table:table-cell":
                self.in_table_cell = False
        self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if not self.keyword_found:
            # look for the table:table-row element, then look for table:table-cell within that
            # element, then look for text:p within that element. Extract name of keyword from
            # xlink:href attribute. Then look for the next table:table-cell element and replace
            # the table:style-name attribute with the correct value according to the status value.
            if name == 'table:table-row':
                self.in_table_row = True
                self.current_keyword = None
            elif self.in_table_row and name == 'table:table-cell':
                if (self.current_keyword is not None) and self.current_keyword == self.keyword:
                    logging.info(f"Found keyword {self.keyword}.")
                    # We have already found the keyword name within this table row
                    if "table:style-name" in attrs.getNames():
                        attrs = {k: v for k, v in attrs.items()}
                        if self.status == KeywordStatus.ORANGE:
                            # Orange table cell has style name "Table35.H9"
                            attrs["table:style-name"] = "Table35.H9"
                        elif self.status == KeywordStatus.GREEN:
                            # Green table cell has style name "Table35.H5"
                            attrs["table:style-name"] = "Table35.H5"
                        else:
                            raise ValueError(f"Invalid status value: {self.status}.")
                        logging.info(f"Successfully changed status of keyword {self.keyword}.")
                        self.current_keyword = None
                        self.in_table_cell = False
                        self.keyword_found = True
                else:
                    self.in_table_cell = True
            elif self.in_table_cell and name == 'text:a':
                if "xlink:href" in attrs.getNames():
                    href = attrs.getValue("xlink:href")
                    # the href value is on the form "#1.2.1.ACTDIMS – ACTION Keyword Dimensions"
                    # we want to extract the keyword name from this string
                    if match := re.match(r"#\d+.\d+.\d+.(\w+)\s+", href):
                        self.current_keyword = match.group(1)
        self.content.write(XMLHelper.starttag(name, attrs))


class UpdateKeywordStatus:
    def __init__(self, maindir: str, keyword: str, status: KeywordStatus) -> None:
        self.keyword = keyword
        self.status = status
        self.maindir = maindir

    def update(self) -> None:
        self.filename = Path(self.maindir) / Directories.appendices / f"A.{FileExtensions.fodt}"
        if not self.filename.is_file():
            raise FileNotFoundError(f"File {self.filename} not found.")
        # parse the xml file
        parser = xml.sax.make_parser()
        handler = AppendixStatusColorHandler(self.keyword, self.status)
        parser.setContentHandler(handler)
        parser.parse(self.filename)
        if handler.keyword_found:
            # Take a backup of the file
            tempfile_ = tempfile.mktemp()
            shutil.copy(self.filename, tempfile_)
            logging.info(f"Created backup of {self.filename} in {tempfile_}.")
            # write handler content to file
            with open(self.filename, "w", encoding='utf8') as f:
                f.write(handler.content.getvalue())
            logging.info(f"Wrote updated file to {self.filename}.")
        else:
            logging.info(f"Keyword {self.keyword} not found in {self.filename}.")

@click.command()
@ClickOptions.maindir(required=False)
@click.option("--keyword", type=str, required=True, help="Keyword to change status for.")
@click.option("--status", type=str, required=True, help="New status for keyword.")
def set_keyword_status(maindir: str, keyword: str, status: str) -> None:
    """Change the status of a keyword in Appendix A."""
    logging.basicConfig(level=logging.INFO)
    try:
        status = KeywordStatus[status.upper()]
    except ValueError:
        raise ValueError(f"Invalid status value: {status}.")
    logging.info(f"Setting status of keyword {keyword} to {status}.")
    UpdateKeywordStatus(maindir, keyword, status).update()

if "__name__" == "__main__":
    set_keyword_status()