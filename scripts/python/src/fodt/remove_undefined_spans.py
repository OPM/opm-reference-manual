import io
import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions
from fodt import xml_helpers


class RemoveSpanHandler(xml.sax.handler.ContentHandler):
    # Within the sections before the office:body starts, record the style:name attribute of
    # all elements (to be sure not to miss any)
    # Then, when parsing the office:body section, remove all text:span elements that
    # have a style-name attribute that is not in the recorded set.
    # NOTE: This will not remove span tags outside the office:body section yet. For
    #  example inside the office:master-styles section.
    def __init__(self) -> None:
        self.content = io.StringIO()
        self.in_body = False
        self.in_span = False
        self.start_tag_open = False  # For empty tags, do not close with />
        self.styles = set()  # All style names found before the office:body section
        self.removed_styles = set() # All style names that are removed
        self.num_removed_spans = 0  # Number of removed span tags
        # NOTE: we do not handle nested spans, so only the outermost span is
        # currently removed
        self.span_recursion = 0

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(xml_helpers.escape(content))

    def endElement(self, name: str):
        if name == "office:body":
            self.in_body = False
        elif self.in_body and name == "text:span" and self.in_span:
            if self.span_recursion > 0:
                self.span_recursion -= 1
            else:
                self.in_span = False
                self.num_removed_spans += 1
                return # remove this tag
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(xml_helpers.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_location(self) -> str:
        if hasattr(self, "locator"):
            return f"[{self.locator.getLineNumber()}:{self.locator.getColumnNumber()}]"
        else:
            return "unknown location"

    def get_removed_styles(self) -> set[str]:
        return self.removed_styles

    def get_num_removed_spans(self) -> int:
        return self.num_removed_spans

    # This callback is used for debugging, it can be used to print
    #  line numbers in the XML file
    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        self.content.write(xml_helpers.HEADER)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")
            self.start_tag_open = False
        if name == "office:body":
            self.in_body = True
        elif not self.in_body:  # Before the office:body section
            if attrs.get("style:name"):
                self.styles.add(attrs.get("style:name"))
        elif self.in_body and name == "text:span":
            if self.in_span:
                self.span_recursion += 1
            elif attrs.get("text:style-name"):
                span_style_name = attrs.get("text:style-name")
                if span_style_name not in self.styles:
                    self.in_span = True
                    self.span_recursion = 0
                    self.removed_styles.add(span_style_name)
                    #logging.info(f"removing span: {span_style_name}")
                    return  # remove this tag
        self.start_tag_open = True
        self.content.write(xml_helpers.starttag(name, attrs, close_tag=False))


class RemoveSpanTags:
    def __init__(self, maindir: str, filename: str|None, max_files: int|None) -> None:
        self.maindir = Path(maindir)
        self.filename = filename
        self.max_files = max_files

    def remove_span_tags(self) -> None:
        if self.filename:
            self.remove_span_tags_from_file(self.maindir / self.filename)
        else:
            self.remove_span_tags_from_all_files()

    def remove_span_tags_from_all_files(self) -> None:
        for i, filename in enumerate(self.maindir.rglob("*.fodt"), start=1):
            if self.max_files and i > self.max_files:
                break
            logging.info(f"Processing file {i}: {filename}")
            self.remove_span_tags_from_file(filename)

    def remove_span_tags_from_file(self, filename: Path) -> None:
        parser = xml.sax.make_parser()
        handler = RemoveSpanHandler()
        parser.setContentHandler(handler)
        parser.parse(filename)
        removed_styles = handler.get_removed_styles()
        num_removed_spans = handler.get_num_removed_spans()
        if len(removed_styles) > 0:
            with open(filename, "w", encoding='utf8') as f:
                f.write(handler.get_content())
            logging.info(f"Removed {num_removed_spans} span tags from {filename}")

# USAGE:
#
#   fodt-remove-undefined-span-tags \
#        --maindir=<main directory> \
#        --filename=<filename> \
#        --max-files=<max files>
#
# DESCRIPTION:
#
#   Removes undefined span tags from a given .fodt file, or, if --filename is not
#   specified, from all .fodt subdocuments in the specified main directory.
#   A span tag is considered undefined if it refers to a style name that is not
#   defined in the document.
#   In case, --filename option is not given, the max-files option can be used to
#   limit the number of files that will be processed. If not given, all files are processed.
#
@click.command()
@ClickOptions.maindir(required=False)
@click.option("--filename", type=str, help="Name of the file to process.", required=False)
@click.option(
    "--max-files",
    type=int,
    help="Maximum number of files to process.",
    required=False,
)
def remove_undefined_span_tags(
    maindir: str, filename: str|None, max_files: int|None
) -> None:
    """Remove unused span tags from .fodt subdocuments."""
    logging.basicConfig(level=logging.INFO)
    RemoveSpanTags(maindir, filename, max_files).remove_span_tags()
