import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path
from typing import Callable

from fodt.xml_helpers import XMLHelper
from fodt.exceptions import HandlerDoneException, InputException, ParsingException
from fodt.helpers import Helpers

class PartsHandler(xml.sax.handler.ContentHandler):
    def __init__(
        self,
        outputfn: str,
        chapter: int,
        section: int,
        keywords: list[str],
        replace_callback: Callable[[str], str] | None,
    ) -> None:
        self.outputfn = outputfn
        self.chapter = chapter
        self.section = section
        self.keywords = keywords
        self.current_section = 0
        self.current_subsection = 0
        if replace_callback is None:
            replace_callback = self.default_replace_callback
        self.replace_callback = replace_callback
        self.content = io.StringIO()
        self.in_subsection = False
        self.done = False
        self.remove_section = False
        self.in_main_section = False

    def characters(self, content: str):
        # if (not self.in_subsection) and (not self.remove_section):
        if not self.in_main_section:
            self.content.write(xml.sax.saxutils.escape(content))

    def check_included_section(self, name: str, attrs: xml.sax.xmlreader.AttributesImpl) -> bool:
        if "text:name" in attrs.getNames():
            name = attrs.getValue("text:name")
            if name.startswith(f"Section{self.chapter}.{self.section}:"):
                return True
        return False

    def default_replace_callback(self, section: int) -> str:
        return f"<text:section>Section{section}</text:section>\n"

    def endElement(self, name: str):
        if name == "text:section":
            if (not self.remove_section) and self.in_main_section:
                self.in_subsection = False
                self.insert_remaining_subsections()
                self.done = True
                self.in_main_section = False
        if (not self.in_subsection) and (not self.remove_section):
            self.content.write(XMLHelper.endtag(name))
        if name == "text:section":
            if self.remove_section:
                self.remove_section = False

    def endDocument(self) -> None:
        self.write_file()

    def insert_remaining_subsections(self) -> None:
        for i in range(self.current_subsection, len(self.keywords)):
            subsection = i + 1
            part = f"{self.chapter}.{self.section}.{subsection}"
            keyword = self.keywords[i]
            callback = self.replace_callback
            self.content.write(callback(part, keyword))

    def startDocument(self):
        self.write_xml_header()

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        write_include = False
        if not self.done:
            if name == "text:h":
                if "text:outline-level" in attrs.getNames():
                    level = attrs.getValue("text:outline-level")
                    if level == "2":
                        self.current_subsection = 0
                        if self.in_subsection:
                            self.in_subsection = False
                            self.done = True
                        else:
                            self.current_section += 1
                    elif level == "3":
                        self.current_subsection += 1
                        if self.in_subsection:
                            write_include = True
                        else:
                            if self.current_section == self.section:
                                self.in_subsection = True
                                write_include = True
            elif name == "text:section":
                if self.check_included_section(name, attrs):
                    self.remove_section = True
                    self.in_main_section = True
        if write_include:
            self.in_main_section = True
            part = f"{self.chapter}.{self.section}.{self.current_subsection}"
            keyword = self.keywords[self.current_subsection - 1]
            callback = self.replace_callback
            self.content.write(callback(part, keyword))
        if (not self.in_subsection) and (not self.remove_section):
            self.content.write(XMLHelper.starttag(name, attrs))

    def write_file(self):
        filename = Path(self.outputfn)
        with open(filename, "w", encoding='utf8') as f:
            f.write(self.content.getvalue())
        self.content = None
        logging.info(f"Wrote modified file to file {filename}.")

    def write_xml_header(self) -> None:
        self.content.write(XMLHelper.header)


class RemoveSubSections():
    def __init__(
        self,
        filename: str,
        outputfn: str,
        chapter: int,
        section: int,
        replace_callback: Callable[[str], str] | None = None,
    ) -> None:
        logging.info(f"Removing parts from {filename}.")
        outputdir = Path(outputfn).parent
        keywords = Helpers.read_keyword_order(outputdir, chapter, section)
        parser = xml.sax.make_parser()
        handler = PartsHandler(outputfn, chapter, section, keywords, replace_callback)
        parser.setContentHandler(handler)
        try:
            parser.parse(filename)
        except HandlerDoneException as e:
            logging.info(e)
        logging.info(f"Done removing special parts.")
