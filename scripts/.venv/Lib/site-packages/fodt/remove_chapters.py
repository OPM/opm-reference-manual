import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path
from typing import Callable

from fodt.exceptions import HandlerDoneException, InputException
from fodt.xml_helpers import XMLHelper

class ChapterHandler(xml.sax.handler.ContentHandler):
    def __init__(
        self,
        outputfn: str,
        chapters: list[int],
        replace_callback: Callable[[int], str] | None,
    ) -> None:
        self.outputfn = outputfn
        self.chapters = chapters
        self.current_section = 0
        self.next_section = self.chapters.pop(0)
        self.outline_level = "1"
        if replace_callback is None:
            replace_callback = self.default_replace_callback
        self.replace_callback = replace_callback
        # NOTE: we will use io.StringIO for this, since appending
        #   is much faster than appending to a string. See: https://waymoot.org/home/python_string/
        self.content = io.StringIO()
        self.in_section = False
        self.found_appendix = False

    def characters(self, content: str):
        if not self.in_section:
            self.content.write(XMLHelper.escape(content))

    def default_replace_callback(self, section: int) -> str:
        return f"<text:section>Section{section}</text:section>\n"

    def endElement(self, name: str):
        if not self.in_section:
            self.content.write(XMLHelper.endtag(name))

    def endDocument(self) -> None:
        self.write_file()

    def startDocument(self):
        self.write_xml_header()

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if not self.found_appendix:
            if self.start_of_appendix(name, attrs):
                self.current_section += 1
                self.in_section = False
                self.found_appendix = True
            elif name == "text:h":
                if "text:outline-level" in attrs.getNames():
                    level = attrs.getValue("text:outline-level")
                    if level == self.outline_level:
                        self.current_section += 1
                        if self.current_section == self.next_section:
                            self.in_section = True
                            callback = self.replace_callback
                            self.content.write(callback(self.current_section))
                            if len(self.chapters) > 0:
                                self.next_section = self.chapters.pop(0)
                        else:
                            self.in_section = False
        if not self.in_section:
            self.content.write(XMLHelper.starttag(name, attrs))

    def start_of_appendix(self, name: str, attrs: xml.sax.xmlreader.AttributesImpl) -> bool:
        if name == "text:list":
            if "text:style-name" in attrs.getNames():
                style = attrs.getValue("text:style-name")
                if style == "_40_Appendix_20_Heading_20_Numbering":
                    logging.info("Found start of appendix, will not remove any more parts.")
                    return True
        return False

    def write_file(self):
        filename = Path(self.outputfn)
        dir_ = filename.parent
        dir_.mkdir(parents=True, exist_ok=True)
        with open(filename, "w", encoding='utf8') as f:
            f.write(self.content.getvalue())
        self.content = None
        logging.info(f"Wrote modified file to file {filename}.")

    def write_xml_header(self) -> None:
        self.content.write(XMLHelper.header)

class RemoveChapters():
    def __init__(
        self,
        outputfn: str,
        filename: str,
        chapters: list[int],
        replace_callback: Callable[[int], str] | None = None,
    ) -> None:
        logging.info(f"Removing chapters {chapters} from {filename}.")
        parser = xml.sax.make_parser()
        if len(chapters) == 0:
            raise InputException("No chapter numbers specified.")
        if min(chapters) < 1:
            raise InputException("Chapter numbers should be >= 1.")
        handler = ChapterHandler(outputfn, chapters, replace_callback)
        parser.setContentHandler(handler)
        try:
            logging.info(f"Parsing {filename}.")
            parser.parse(filename)
        except HandlerDoneException as e:
            logging.info(e)
        logging.info(f"Done removing chapters.")
