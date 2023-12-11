import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

from fodt.constants import TagEvent
from fodt.exceptions import HandlerDoneException
from fodt.xml_helpers import XMLHelper

class ElementHandler(xml.sax.handler.ContentHandler):
    def __init__(self, outputfn: str, count: int, name: str) -> None:
        self.tag_name = name
        logging.info(f"tag_name: {self.tag_name}")
        self.outputfn = outputfn
        self.count = count
        self.current_element = 0
        self.done_removing = False
        self.nesting = None
        # NOTE: we will use io.StringIO for this, since appending
        #   is much faster than appending to a string. See: https://waymoot.org/home/python_string/
        self.content = io.StringIO()
        # TODO: setting to True does not work yet, since some whitespace is significant
        #   in the body section of fodt file.
        #   We need to find a way to remove the whitespace that is insignificant.
        self.in_element = False

    def startDocument(self):
        self.write_xml_header()

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if (not self.done_removing) and (name == self.tag_name):
            if not self.in_element:  # recursive elements not supported yet
                self.current_element += 1
                self.nesting = 1
                self.in_element = True
                logging.info(f"Starting to remove element {self.tag_name}.")
            else:
                self.nesting += 1
        if self.done_removing or (not self.in_element):
            self.content.write(XMLHelper.starttag(name, attrs))

    def endElement(self, name: str):
        if not self.in_element:
            self.content.write(XMLHelper.endtag(name))
        else:
            if name == self.tag_name:
                self.nesting -= 1
                if self.nesting == 0:
                    self.in_element = False
                    if self.current_element >= self.count:
                        self.done_removing = True
                elif self.nesting < 0:
                    raise Exception("nesting should never be < 0")

    def endDocument(self) -> None:
        self.write_file()

    def characters(self, content: str):
        if not self.in_element:
            self.content.write(xml.sax.saxutils.escape(content))

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

class RemoveElements():
    def __init__(self, name: str, outputfn: str, filename: str, count: int) -> None:
        logging.info(f"Removing {count} elements with name {name} from {filename}.")
        parser = xml.sax.make_parser()
        handler = ElementHandler(outputfn, count, name)
        parser.setContentHandler(handler)
        try:
            logging.info(f"Parsing {filename}.")
            parser.parse(filename)
        except HandlerDoneException as e:
            logging.info(e)
        logging.info(f"Done removing special parts.")
