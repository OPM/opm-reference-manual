import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

from fodt.constants import Directories, FileNames
from fodt.exceptions import HandlerDoneException
from fodt.xml_helpers import XMLHelper

class TagHandler(xml.sax.handler.ContentHandler):
    def __init__(self, tag_name: str) -> None:
        self.tag_name = tag_name
        self.attrs = {}

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if name == self.tag_name:
            for (key, value) in attrs.items():
                self.attrs.update({key: value})
            raise HandlerDoneException(f"Done parsing. Found tag {name}.")

    def get_attrs(self) -> dict:
        return self.attrs


class ExtractTagAttrs():
    def __init__(self, filename: str, xml_tag: str) -> None:
        logging.info(f"Extracting attributes from tag {xml_tag} from {filename}.")
        parser = xml.sax.make_parser()
        self.handler = TagHandler(xml_tag)
        parser.setContentHandler(self.handler)
        try:
            logging.info(f"Parsing {filename}.")
            parser.parse(filename)
        except HandlerDoneException as e:
            pass

    def get_attrs(self) -> dict:
        return self.handler.get_attrs()


class ExtractDocAttrs():
    def __init__(self, maindir: str, filename: str) -> None:
        extracter = ExtractTagAttrs(filename, xml_tag="office:document")
        attrs = extracter.get_attrs()
        outputdir = Path(maindir) / Directories.meta
        outputdir.mkdir(parents=True, exist_ok=True)
        filename = outputdir / FileNames.office_attr_fn
        if filename.exists():
            logging.info(
                f"Warning: Document attributes file {filename} already exists, "
                f"will overwrite...")
        with open(filename, "w", encoding='utf-8') as f:
            for (key, value) in attrs.items():
                evalue = XMLHelper.escape(value)
                f.write(f'{key}="{evalue}"\n')
        logging.info(f"Wrote document attributes to {filename}.")
