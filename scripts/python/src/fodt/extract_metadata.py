import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

from fodt.constants import Directories, MetaSections, TagEvent
from fodt.exceptions import HandlerDoneException
from fodt.xml_helpers import XMLHelper

class SectionHandler(xml.sax.handler.ContentHandler):
    def __init__(self, outputdir: str) -> None:
        self.outputdir = outputdir
        self.section_names = MetaSections.names
        self.current_section = None
        self.sections = {item for item in self.section_names}
        # NOTE: we will use io.StringIO for these two strings, since appending
        #   is much faster than appending to a string. See: https://waymoot.org/home/python_string/
        self.section = None
        self.content = None
        self.enable_indent = False
        self.indent = 0
        self.last_event = TagEvent.NONE
        self.in_section = False

    def add_indent(self, new_file: bool) -> str:
        if new_file:
            return ""
        if self.enable_indent:
            return "\n" + (" " * self.indent)
        return ""

    def add_previous_content(self, content: io.StringIO | None) -> None:
        if content is not None:
            if self.enable_indent:
                content = re.sub(r"\s+$", "", content.getvalue())
            else:
                content = content.getvalue()
            self.section.write(content)

    def add_section_start(
        self,
        prev_content: str,
        name:str,
        attrs: xml.sax.xmlreader.AttributesImpl,
        new_file: bool
    ) -> None:
        self.add_previous_content(prev_content)
        self.section.write(f"{self.add_indent(new_file)}")
        self.section.write(XMLHelper.starttag(name, attrs))
        self.indent += 1

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if name in self.sections or self.in_section:
            self.last_event = TagEvent.START
            previous_content = self.content
            self.content = io.StringIO()
            new_file = False
            if name in self.sections:
                self.current_section = name
                self.in_section = True
                self.sections.remove(name)
                self.section = io.StringIO()
                new_file = True
                # logging.info(f"Found section {name}.")
            self.add_section_start(previous_content, name, attrs, new_file)

    def endElement(self, name: str):
        if self.in_section:
            last_event = self.last_event
            self.last_event = TagEvent.END
            self.indent -= 1
            prev_content = self.content
            self.content = io.StringIO()
            self.add_previous_content(prev_content)
            if last_event == TagEvent.END:
                if self.enable_indent:
                    self.section.write("\n" + (" " * self.indent))
            self.section.write(XMLHelper.endtag(name))
        if name == self.current_section:
            self.in_section = False
            self.write_section_to_file()
            self.current_section = None
            if len(self.sections) == 0:
                raise HandlerDoneException(f"Done extracting sections.")

    def characters(self, content: str):
        if self.in_section:
            self.content.write(XMLHelper.escape(content))

    def write_section_to_file(self):
        filename = self.current_section.removeprefix("office:") + ".xml"
        dir_ = Path(self.outputdir) / Directories.meta_sections
        dir_.mkdir(parents=True, exist_ok=True)
        path = dir_ / filename
        if path.exists():
            logging.info(
                f"Warning: Section {self.current_section} : "
                f"File {filename} already exists, will overwrite..")
        with open(path, "w", encoding='utf-8') as f:
            f.write(self.section.getvalue())
        logging.info(f"Wrote section {self.current_section} to file {filename}.")
        self.section = None

class ExtractMetaData():
    def __init__(self, maindir:str, filename: str) -> None:
        logging.info(f"Extracting metadata from {filename}.")
        parser = xml.sax.make_parser()
        outputdir = Path(maindir) / Directories.meta
        handler = SectionHandler(outputdir)
        parser.setContentHandler(handler)
        try:
            logging.info(f"Parsing {filename}.")
            parser.parse(filename)
        except HandlerDoneException as e:
            pass
        logging.info(f"Done extracting metadata.")

