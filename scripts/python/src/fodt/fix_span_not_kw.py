import io
import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions, FileExtensions, Directories
from fodt.exceptions import HandlerDoneException
from fodt import helpers
from fodt.xml_helpers import XMLHelper


class FileHandler(xml.sax.handler.ContentHandler):
    def __init__(self, keyword_name: str, only_check_changed: bool) -> None:
        # If only_check_changed is True, we only check if the file needs to be changed
        #  and abort the parsing as soon as we know that the file needs to be changed.
        self.only_check = only_check_changed
        self.keyword_name = keyword_name
        self.content = io.StringIO()
        self.in_body = False
        self.in_office_styles = False
        # True if the style "NotKeyword" is found in the office:styles section
        self.found_not_kw_style = False
        # For empty tags, we use a special trick to rewrite them with a shortened
        #  end /> tag instead of the full end tag </tag>
        self.start_tag_open = False
        self._file_changed = False

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(XMLHelper.escape(content))

    def endElement(self, name: str):
        if name == "office:styles":
            assert self.start_tag_open == False  # Should not happen for this tag
            if not self.found_not_kw_style:
                self.content.write(
                    """ <style:style style:name="NotKeyword" style:family="text"/>\n """
                )
            self.in_office_styles = False
            self.content.write(XMLHelper.endtag(name))
            return
        elif name == "office:body":
            self.in_body = False
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def file_changed(self) -> bool:
        return self._file_changed

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_location(self) -> str:
        if hasattr(self, "locator"):
            return f"[{self.locator.getLineNumber()}:{self.locator.getColumnNumber()}]"
        else:
            return "unknown location"

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
        if name == "office:styles":
            self.in_office_styles = True
        elif name == "office:body":
            self.in_body = True
        elif self.in_body and name == "text:span":
            if attrs.get("text:style-name"):
                span_style_name = attrs.get("text:style-name")
                if span_style_name == "NOT_KEYWORD":
                    attrs = dict(attrs)
                    attrs["text:style-name"] = "NotKeyword"
                    self._file_changed = True
                    if self.only_check:
                        raise HandlerDoneException(
                            "Done parsing. Found span tag with style NOT_KEYWORD."
                        )
        elif self.in_office_styles and name == "style:style":
            if attrs.get("style:name") == "NotKeyword":
                self.found_not_kw_style = True
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class FixSpanNotKw:
    def __init__(self, maindir: str) -> None:
        self.maindir = Path(maindir)
        assert self.maindir.is_absolute()

    def fix_files(self) -> None:
        kw_dir = self.maindir / Directories.chapters / Directories.subsections
        for item in kw_dir.iterdir():
            if not item.is_dir():
                continue
            logging.info(f"Processing directory: {item}")
            for item2 in item.iterdir():
                if item2.suffix == f".{FileExtensions.fodt}":
                    keyword_name = item2.name.removesuffix(f".{FileExtensions.fodt}")
                    self.fix_file(item2, keyword_name)

    def fix_file(self, filename: Path, keyword_name: str) -> None:
        parser = xml.sax.make_parser()
        handler = FileHandler(keyword_name, only_check_changed=True)
        parser.setContentHandler(handler)
        try:
            parser.parse(str(filename))
        except HandlerDoneException as e:
            pass
        if handler.file_changed():
            handler = FileHandler(keyword_name, only_check_changed=False)
            parser.setContentHandler(handler)
            parser.parse(str(filename))
            with open(filename, "w", encoding='utf8') as f:
                f.write(handler.content.getvalue())
            logging.info(f"{filename.name}: Fixed.")
        else:
            logging.info(f"{filename.name}: No changes.")

# USAGE:
#
#   fodt-fix-span-not-kw \
#        --maindir=<main directory>
#
# DESCRIPTION:
#
#   This script fixes a bug introduced by assuming that libreoffice would not remove/modify
#   a manually inserted span tag on the form <text:span text:style-name="NOT_KEYWORD">...</text:span>
#   The assumption was not correct, we need to do two things to fix this:
#   - Define a custom style for the span tag (the style name should not include underscores or
#     spaces, unless libreoffice will mangle the style name). We choose to change the style name
#     from "NOT_KEYWORD" to "NotKeyword" (camel case).
#   - The custom style on the form <style:style style:name="NotKeyword" style:family="text"/>
#     should be added to the office:styles section in the fodt file.
#   - The span tag should be changed to <text:span text:style-name="NotKeyword">...</text:span>
@click.command()
@ClickOptions.maindir(required=False)
def fix_span_not_kw(maindir: str) -> None:
    logging.basicConfig(level=logging.INFO)
    # Convert maindir to an absolute path
    maindir = helpers.get_maindir(maindir)
    maindir = Path(maindir).absolute()
    assert maindir.is_dir()
    FixSpanNotKw(maindir).fix_files()
