import click
import io
import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

from fodt.constants import ClickOptions
from fodt import xml_helpers

class ContentHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        self.content = io.StringIO()
        self.in_master_page = False  # Inside the the desired style:master-page element
        self.in_footer = False  # Inside the footer element in style:master-page
        self.in_table_cell = False # Inside the table:table-cell element in the footer
        self.in_p_tag = False   # Inside the text:p element in the table:table-cell
        self.found_span = False  # If we found the span with the desired link style
        self.start_tag_open = False  # For empty tags, do not close with />
        self.fixed_style = False  # If we fixed the style

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        if self.in_p_tag:
            if content == "I":
                if not self.found_span:
                    # Insert the desired span tag with internet link style
                    self.content.write(
                        """<text:span text:style-name="Internet_20_link">""" +
                        content + "</text:span>"  # content is "I"
                    )
                    self.fixed_style = True
                    return
        self.content.write(xml_helpers.escape(content))

    def endElement(self, name: str):
        if self.in_p_tag and name == "text:p":
            self.in_p_tag = False
            self.found_span = False
        if self.in_table_cell and name == "table:table-cell":
            self.in_table_cell = False
        if self.in_footer and name == "style:footer":
            self.in_footer = False
        if self.in_master_page and name == "style:master-page":
            self.in_master_page = False
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(xml_helpers.endtag(name))

    def fixed_footer_style(self) -> bool:
        return self.fixed_style

    def get_content(self) -> str:
        return self.content.getvalue()

    def startDocument(self):
        self.content.write(xml_helpers.HEADER)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")  # Close the start tag
            self.start_tag_open = False
        if self.in_p_tag and name == "text:span":
            if attrs.getValue("text:style-name") == "Internet_20_link":
                self.found_span = True
        if self.in_table_cell and name == "text:p":
            self.in_p_tag = True
        if self.in_footer and name == "table:table-cell":
            self.in_table_cell = True
        if self.in_master_page and name == "style:footer":
            self.in_footer = True
        if name == "style:master-page":
            if attrs.getValue("style:name") == "_40_DocumentKeywordPageStyle":
                self.in_master_page = True
        self.start_tag_open = True
        self.content.write(xml_helpers.starttag(name, attrs, close_tag=False))


class FixFooterStyle:
    def __init__(self, maindir: str, filename: Path|None) -> None:
        self.maindir = maindir
        self.filename = filename

    def fixall(self) -> None:
        # Scan all .fodt documents in the maindir, and fix the footer style in each
        for file in Path(self.maindir).rglob("*.fodt"):
            self.fix_file(file)

    def fixup(self) -> None:
        if self.filename:
            self.fix_file(Path(self.maindir) / self.filename)
        else:
            self.fixall()

    def fix_file(self, filename: Path) -> None:
        parser = xml.sax.make_parser()
        handler = ContentHandler()
        parser.setContentHandler(handler)
        parser.parse(filename)
        if handler.fixed_footer_style():
            # Write the content back to file
            with open(filename, "w", encoding='utf_8') as f:
                f.write(handler.get_content())
            logging.info(f"Fixing footer style in {filename}.")

# USAGE:
#
#   fodt-fix-footer-style --maindir </path/to/maindir> --filename <filename>
#
# DESCRIPTION:
#
#  Scan .fodt documents for a master-page style with style:name "_40_DocumentKeywordPageStyle",
#  - If found, find the footer element within, and search for a table:table-cell element
#    within the footer element. If the table:table-cell element contains a text:p element
#    check that the text:p element contains a span with the style "Internet_20_link". If not,
#    insert a span with the style "Internet_20_link" in the text:p element surrounding the
#    text content "I".
#
#  - If <filename> is given, only process that file, else process all .fodt files in <maindir>.
#  - <filename> must be relative to <maindir>.
#
@click.command()
@ClickOptions.maindir(required=False)
@click.option(
    "--filename",
    required=False,
    help="Filename to fix.",
)
def fix_footer_style(maindir: str, filename: Path|None) -> None:
    """Remove bookmark refs from the master style section in all subdocuments."""
    logging.basicConfig(level=logging.INFO)
    FixFooterStyle(maindir, filename).fixup()

if __name__ == "__main__":
    fix_footer_style()
