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

class AppendixKeywordHandler(xml.sax.handler.ContentHandler):
    def __init__(self, keyword: str, status: KeywordStatus, opm_flow: bool) -> None:
        self.keyword = keyword
        self.status = status
        self.opm_flow = opm_flow
        self.in_section = False
        self.in_table_row = False
        self.in_table_cell = False
        self.in_table_cell_p = False
        self.current_tag_name = None
        self.content = io.StringIO()
        self.current_keyword = None
        self.keyword_handled = False
        self.found_table_cell = False
        self.office_body_found = False
        self.in_table_cell_style = False
        self.orange_styles = set()
        self.green_styles = set()
        self.start_tag_open = False  # For empty tags, do not close with />

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        if self.in_table_cell_p:
            if self.opm_flow:
                content = "OPM Flow"
            else:
                content = ""
            self.keyword_handled = True
            self.current_keyword = None
            self.in_table_cell_p = False
            self.found_table_cell = False
        self.content.write(XMLHelper.escape(content))

    def collect_table_cell_styles(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        # collect the style names for orange and green colors
        # assume that attrs belongs to tagname "style:table-cell-properties" within
        # tagname "style:style"
        if "fo:background-color" in attrs.getNames():
            color = attrs.getValue("fo:background-color")
            if color == "#ff950e":
                if self.current_style is not None:
                    self.orange_styles.add(self.current_style)
                else:
                    logging.info(f"Warning: Found orange color without style name.")
            elif color == "#579d1c":
                if self.current_style is not None:
                    self.green_styles.add(self.current_style)
                else:
                    logging.info(f"Warning: Found green color without style name.")


    def endElement(self, name: str):
        if not self.keyword_handled:
            if name == "table:table-row":
                self.in_table_row = False
            elif self.in_table_row and name == "table:table-cell":
                self.in_table_cell = False
            elif self.in_table_cell_style and name == "style:style":
                self.in_table_cell_style = False
        if self.in_table_cell_p and name == "text:p" and self.start_tag_open:
            self.content.write(">")
            self.start_tag_open = False
            self.keyword_handled = True
            self.current_keyword = None
            self.in_table_cell_p = False
            self.found_table_cell = False
            if self.opm_flow:
                content = "OPM Flow"
                self.content.write(XMLHelper.escape(content))
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def handle_table_row(
            self, name: str, attrs: xml.sax.xmlreader.AttributesImpl
    ) -> xml.sax.xmlreader.AttributesImpl:
        # look for the table:table-row element, then look for table:table-cell within that
        # element, then look for text:p within that element. Extract name of keyword from
        # xlink:href attribute. Then look for the next table:table-cell element and replace
        # the table:style-name attribute with the correct value according to the status value.
        if name == 'table:table-row':
            self.in_table_row = True
            self.current_keyword = None
        elif self.in_table_row and name == 'table:table-cell':
            self.in_table_cell = True
            if (self.current_keyword is not None) and self.current_keyword == self.keyword:
                logging.info(f"Found keyword {self.keyword}.")
                # We have already found the keyword name within this table row
                if "table:style-name" in attrs.getNames():
                    attrs = {k: v for k, v in attrs.items()}
                    if self.status == KeywordStatus.ORANGE:
                        attrs["table:style-name"] = self.orange_style
                    elif self.status == KeywordStatus.GREEN:
                        attrs["table:style-name"] = self.green_style
                    else:
                        raise ValueError(f"Invalid status value: {self.status}.")
                    logging.info(f"Successfully changed status of keyword {self.keyword}.")
                    self.found_table_cell = True
        elif self.in_table_cell and name == 'text:a':
            if "xlink:href" in attrs.getNames():
                href = attrs.getValue("xlink:href")
                # the href value is on the form "#1.2.1.ACTDIMS – ACTION Keyword Dimensions"
                # we want to extract the keyword name from this string
                if match := re.match(r"#\d+\.\d+\.\d+\.(\w+[\-–]?)(?:\s+|$|\|outline$)", href):
                    self.current_keyword = match.group(1)
        elif self.in_table_cell and name == 'text:p':
            if self.found_table_cell:
                logging.info(f"Found text:p element for keyword {self.keyword}.")
                # replace the content of the text:p element with the new status
                self.in_table_cell_p = True
        return attrs

    def select_table_cell_styles(self) -> None:
        if len(self.orange_styles) > 0:
            logging.info(f"Found {len(self.orange_styles)} orange styles.")
            self.orange_style = self.orange_styles.pop()
            logging.info(f"Using orange style {self.orange_style}.")
        else:
            logging.info(f"Warning: No orange styles found.")
            self.orange_style = None
        if len(self.green_styles) > 0:
            logging.info(f"Found {len(self.green_styles)} green styles.")
            self.green_style = self.green_styles.pop()
            logging.info(f"Using green style {self.green_style}.")
        else:
            logging.info(f"Warning: No green styles found.")
            self.green_style = None


    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")  # Close the start tag
            self.start_tag_open = False
        if not self.keyword_handled:
            if not self.office_body_found:
                if name == 'style:style':
                    if "style:family" in attrs.getNames():
                        if attrs.getValue("style:family") == "table-cell":
                            self.in_table_cell_style = True
                            self.current_style = attrs.getValue("style:name")
                elif self.in_table_cell_style and name == 'style:table-cell-properties':
                    self.collect_table_cell_styles(attrs)
                elif name == 'office:body':
                    logging.info(f"Found office:body.")
                    self.select_table_cell_styles()
                    self.office_body_found = True
            else:
                attrs = self.handle_table_row(name, attrs)
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class UpdateKeywordStatus:
    def __init__(
        self, maindir: str, keyword: str, status: KeywordStatus, opm_flow: bool
    ) -> None:
        self.keyword = keyword
        self.status = status
        self.maindir = maindir
        self.opm_flow = opm_flow

    def update(self) -> None:
        self.filename = Path(self.maindir) / Directories.appendices / f"A.{FileExtensions.fodt}"
        if not self.filename.is_file():
            raise FileNotFoundError(f"File {self.filename} not found.")
        # parse the xml file
        parser = xml.sax.make_parser()
        handler = AppendixKeywordHandler(self.keyword, self.status, self.opm_flow)
        parser.setContentHandler(handler)
        parser.parse(self.filename)
        if handler.keyword_handled:
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
@click.option("--color", type=str, required=True, help="New status color for keyword.")
@click.option("--opm-flow", type=bool, default=False, is_flag=True, help="Flow specific keyword")
def set_keyword_status(
    maindir: str,
    keyword: str,
    color: str,
    opm_flow: bool
) -> None:
    """Change the status of a keyword in Appendix A."""
    logging.basicConfig(level=logging.INFO)
    try:
        color = KeywordStatus[color.upper()]
    except ValueError:
        raise ValueError(f"Invalid color value: {color}.")
    logging.info(f"Updating parameters for keyword {keyword}:  Color: {color}, flow-specific keyword: {opm_flow}.")
    UpdateKeywordStatus(maindir, keyword, color, opm_flow).update()

if "__name__" == "__main__":
    set_keyword_status()