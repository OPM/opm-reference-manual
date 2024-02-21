import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from fodt.constants import TagEvent
from fodt.exceptions import HandlerDoneException
from fodt.xml_helpers import XMLHelper


class SectionHandler(xml.sax.handler.ContentHandler):
    def __init__(self, section_name: str, enable_indent: bool = True) -> None:
        self.section_name = section_name
        self.section = ''
        self.indent = 0
        self.last_event = TagEvent.NONE
        self.close_tag_count = 0
        self.enable_indent = enable_indent
        self.attrs = {}
        self.in_section = False

    def add_indent(self) -> str:
        if self.enable_indent:
            return "\n" + (" " * self.indent)
        return ""

    def add_section_start(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.enable_indent:
            self.remove_trailing_spaces()
        self.section += f"{self.add_indent()}"
        self.section += XMLHelper.starttag(name, attrs)
        self.indent += 1

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if name == self.section_name or self.in_section:
            self.last_event = TagEvent.START
            if name == self.section_name:
                self.in_section = True
            self.add_section_start(name, attrs)

    def get_section(self) -> str:
        return self.section

    def endElement(self, name: str):
        if self.in_section:
            last_event = self.last_event
            self.last_event = TagEvent.END
            self.indent -= 1
            if self.enable_indent:
                self.remove_trailing_spaces()
                if last_event == TagEvent.END:
                    self.section += "\n" + (" " * self.indent)
            self.section += XMLHelper.endtag(name)
        if name == self.section_name:
            self.in_section = False
            raise HandlerDoneException(f"Done extracting sections {self.section_name}.")

    def characters(self, content: str):
        if self.in_section:
            self.section += xml.sax.saxutils.escape(content)

    def remove_trailing_spaces(self):
        self.section = re.sub(r"\s+$", "", self.section)

class ExtractXmlTag():
    def __init__(
        self, filename: str, section_name: str, enable_indent: bool = True
    ) -> None:
        self.filename = filename
        self.section_name = section_name
        self.enable_indent = enable_indent

    def extract(self) -> str:
        parser = xml.sax.make_parser()
        handler = SectionHandler(self.section_name, enable_indent=self.enable_indent)
        parser.setContentHandler(handler)
        try:
            logging.info(f"Parsing {self.filename}.")
            parser.parse(self.filename)
        except HandlerDoneException as e:
            logging.info(e)
        return handler.get_section()
