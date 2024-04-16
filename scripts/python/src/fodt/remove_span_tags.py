import io
import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions
from fodt.helpers import Helpers
from fodt.xml_helpers import XMLHelper

class RemoveEmptyLinesHandler(xml.sax.handler.ContentHandler):
    # Within the office:automatic-styles section, remove empty lines left behind
    # by the RemovedStylesHandler.

    def __init__(self) -> None:
        self.content = io.StringIO()
        self.in_auto_styles = False
        self.in_tag = False  # Within a tag in the automatic-styles section
        self.tag_recursion = 0  # Recursion level within the tag
        self.start_tag_open = False  # For empty tags, do not close with />
        self.save_space = ""  # See comments for characters() below

    def characters(self, content: str):
        # Check if we are at the top level of the automatic-styles section
        if self.in_auto_styles and not self.in_tag:
            # This should only happen after an end tag and before a start tag
            if content.isspace():
                # We need to accumulate the content since characters() does not
                # provide all the space between an end tag of an element and the
                # beginning of the start tag of an element in on call, it chunks
                # the space into multiple calls..
                # Then, we will actually remove the space in the beginning of
                # startElement()..
                self.save_space += content
                return  # Do not write the space to the content yet..
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(XMLHelper.escape(content))

    def endElement(self, name: str):
        if self.in_auto_styles:
            if self.in_tag:
                self.tag_recursion -= 1
                if self.tag_recursion == 0:
                    # We are at the top level of the automatic-styles section
                    self.in_tag = False
        if name == "office:automatic-styles":
            self.in_auto_styles = False
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    # This callback is used for debugging, it can be used to print
    #  line numbers in the XML file
    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")  # Close the start tag
            self.start_tag_open = False
        if self.in_auto_styles and not self.in_tag:
            if len(self.save_space) > 0:
                if '\n' in self.save_space:
                    index = self.save_space.rfind("\n")
                    if index != -1:
                        # Remove the space left behind by the removed style tag
                        self.save_space = self.save_space[index:]
                self.content.write(self.save_space)
                self.save_space = ""
        if name == "office:automatic-styles":
            self.in_auto_styles = True
        elif self.in_auto_styles:
            self.in_tag = True
            self.tag_recursion += 1
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class RemoveStylesHandler(xml.sax.handler.ContentHandler):
    # Within the office:automatic-styles section, remove the rsid styles that
    # corresponds to the span tags that were removed in the previous iteration.

    def __init__(self, removed_styles: set[str]) -> None:
        self.removed_styles = removed_styles
        self.content = io.StringIO()
        self.in_auto_styles = False
        self.start_tag_open = False  # For empty tags, do not close with />
        # NOTE: Assume that the style:style tag does not contain nested style:style tags
        #  so we omit recursion handling here..
        self.in_style = False

    def characters(self, content: str):
        if self.in_style:
            return # remove this tag
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(XMLHelper.escape(content))

    def endElement(self, name: str):
        if self.in_style:
            if name == "style:style":
                self.in_style = False
            return # remove this tag
        if name == "office:automatic-styles":
            self.in_auto_styles = False
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
        if self.in_style:
            return # remove this tag
        if self.start_tag_open:
            self.content.write(">")
            self.start_tag_open = False
        if name == "office:automatic-styles":
            self.in_auto_styles = True
        elif self.in_auto_styles and  name == "style:style":
            if attrs.get("style:name"):
                style_name = attrs.get("style:name")
                if style_name in self.removed_styles:
                    self.in_style = True
                    return # remove this tag
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class RemoveSpanHandler(xml.sax.handler.ContentHandler):
    # Within the office:automatic-styles section, record the style:name attribute of
    # all the style:style elements that has an inner style:text-properties element with
    # attribute officeooo:rsid.
    # Then when parsing the office:body section, remove all text:span elements that
    # have the style-name attribute set to one of the recorded style:name values.
    # NOTE: This will not remove span tags outside the office:body section yet. For
    #  example inside the office:master-styles section.
    def __init__(self) -> None:
        self.content = io.StringIO()
        self.in_body = False
        self.in_span = False
        self.in_style = False
        self.in_auto_styles = False
        self.start_tag_open = False  # For empty tags, do not close with />
        self.rsid_styles = set()  # All rsid style names
        self.removed_styles = set() # All rsid style names that are removed
        # NOTE: we do not handle nested spans, so only the outermost span is
        # currently removed
        self.span_recursion = 0

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(XMLHelper.escape(content))

    def endElement(self, name: str):
        if name == "office:automatic-styles":
            self.in_auto_styles = False
        elif self.in_style and name == "style:style":
            self.in_style = False
        elif name == "office:body":
            self.in_body = False
        elif self.in_body and name == "text:span" and self.in_span:
            if self.span_recursion > 0:
                self.span_recursion -= 1
            else:
                self.in_span = False
                return # remove this tag
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_location(self) -> str:
        if hasattr(self, "locator"):
            return f"[{self.locator.getLineNumber()}:{self.locator.getColumnNumber()}]"
        else:
            return "unknown location"

    def get_removed_styles(self) -> set[str]:
        return self.removed_styles

    # This callback is used for debugging, it can be used to print
    #  line numbers in the XML file
    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")
            self.start_tag_open = False
        if name == "office:automatic-styles":
            self.in_auto_styles = True
        elif self.in_auto_styles and  name == "style:style":
            if attrs.get("style:name"):
                self.style_name = attrs.get("style:name")
                #logging.info(f"style_name: {self.style_name}")
                self.in_style = True
        elif self.in_style and name == "style:text-properties":
            if attrs.get("officeooo:rsid"):
                #logging.info(f"adding style_name: {self.style_name}")
                self.rsid_styles.add(self.style_name)
        elif name == "office:body":
            self.in_body = True
        elif self.in_body and name == "text:span":
            if self.in_span:
                self.span_recursion += 1
            elif attrs.get("text:style-name"):
                span_style_name = attrs.get("text:style-name")
                if span_style_name in self.rsid_styles:
                    self.in_span = True
                    self.span_recursion = 0
                    self.removed_styles.add(span_style_name)
                    #logging.info(f"removing span: {span_style_name}")
                    return  # remove this tag
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class RemoveSpanTags:
    def __init__(self, maindir: str, filename: str|None, max_files: int|None) -> None:
        self.maindir = Path(maindir)
        self.filename = filename
        self.max_files = max_files
        assert self.maindir.is_absolute()
        assert self.filename is None or Path(self.filename).is_absolute()
        assert self.maindir.is_dir()

    def remove_empty_lines(self, filename: Path) -> None:
        # Remove empty lines from the automtic-styles section
        parser = xml.sax.make_parser()
        handler = RemoveEmptyLinesHandler()
        parser.setContentHandler(handler)
        parser.parse(filename)
        with open(filename, "w", encoding='utf8') as f:
            f.write(handler.get_content())

    def remove_span_tags(self) -> None:
        if self.filename:
            # NOTE: self.filename is an absolute path
            self.remove_span_tags_and_styles_from_file(self.filename)
        else:
            self.remove_span_tags_from_all_files()

    def remove_span_tags_from_all_files(self) -> None:
        for i, filename in enumerate(self.maindir.rglob("*.fodt"), start=1):
            if self.max_files and i > self.max_files:
                break
            logging.info(f"Processing file {i}: {filename}")
            self.remove_span_tags_and_styles_from_file(filename)

    def remove_rsid_styles(self, filename: Path, removed_styles: set[str]) -> None:
        parser = xml.sax.make_parser()
        handler = RemoveStylesHandler(removed_styles)
        parser.setContentHandler(handler)
        parser.parse(filename)
        with open(filename, "w", encoding='utf8') as f:
            f.write(handler.get_content())

    def remove_span_tags_and_styles_from_file(self, filename: Path) -> None:
        # We do this in three steps:
        # - first we remove the span tags, then
        # - we remove the corresponding rsid styles from the automatic-styles section, and
        # - finally we remove whitespace empty lines from the file.
        #
        # Why do we need step #3? Because empty lines can be created due to the
        # indentation of the removed style tags in step #2 above.
        removed_styles = self.remove_span_tags_from_file(filename)
        if len(removed_styles) > 0:
            self.remove_rsid_styles(filename, removed_styles)
            self.remove_empty_lines(filename)
            logging.info(f"Removed {len(removed_styles)} styles")
        else:
            logging.info(f"No styles removed")

    def remove_span_tags_from_file(self, filename: Path) -> set[str]:
        parser = xml.sax.make_parser()
        handler = RemoveSpanHandler()
        parser.setContentHandler(handler)
        parser.parse(filename)
        removed_styles = handler.get_removed_styles()
        if len(removed_styles) > 0:
            with open(filename, "w", encoding='utf8') as f:
                f.write(handler.get_content())
        return removed_styles

# USAGE:
#
#   fodt-remove-version-span-tags \
#        --maindir=<main directory> \
#        --filename=<filename> \
#        --max-files=<max files>
#
# DESCRIPTION:
#
#   Removes the version span tags from a given .fodt file, or, if --filename is not
#   specified, from all .fodt subdocuments in the specified main directory.
#   In case, --filename option is not given, the max-files option can be used to
#   limit the number of files that will be processed. If not given, all files are processed.
#
#   For background information on why this is needed see:
#
#   https://ask.libreoffice.org/t/where-do-the-text-style-name-tnn-span-tags-come-from-and-how-do-i-get-rid-of-them/31681
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
def remove_version_span_tags(
    maindir: str, filename: str|None, max_files: int|None
) -> None:
    """Remove version span tags from all .fodt subdocuments."""
    logging.basicConfig(level=logging.INFO)
    if filename is not None:
        filename = Path(filename)
        assert filename.is_absolute()
        maindir, filename = Helpers.locate_maindir_and_filename(maindir, filename)
    else:
        # Convert maindir to an absolute path
        maindir = Helpers.get_maindir(maindir)
        maindir = Path(maindir).absolute()
        assert maindir.is_dir()
    RemoveSpanTags(maindir, filename, max_files).remove_span_tags()
