import base64
import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

import click

from fodt.exceptions import HandlerDoneException

class FontHandler(xml.sax.handler.ContentHandler):
    def __init__(self, save_dir: Path) -> None:
        self.save_dir = save_dir
        self.in_section = False
        self.in_font_face = False
        self.in_font_face_src = False
        self.in_binary_data = False
        self.font_data = io.StringIO()
        self.font_name = None
        self.font_family = None
        # self.font_family_generic = None
        self.font_style = None
        self.font_weight = None

    def characters(self, content: str):
        if self.in_binary_data:
            self.font_data.write(xml.sax.saxutils.escape(content))

    def endElement(self, name: str):
        if self.in_binary_data and name == 'office:binary-data':
            self.in_binary_data = False
            self.write_font_data_to_file()
            self.font_data = io.StringIO()
            self.font_name = None
            self.font_family = None
            # self.font_family_generic = None
            self.font_style = None
            self.font_weight = None
        elif self.in_font_face_src and name == 'svg:font-face-uri':
            self.in_font_face_src = False
        elif self.in_font_face and name == 'style:font-face':
            self.in_font_face = False
        elif self.in_section and name == 'office:font-face-decls':
            self.in_section = False
            raise HandlerDoneException(f"Done extracting fonts.")

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if name == 'office:font-face-decls':
            self.in_section = True
            return
        if self.in_section:
            if name == 'style:font-face':
                self.in_font_face = True
                self.font_name = attrs.getValue('style:name')
                self.font_family = attrs.getValue('svg:font-family')
                #self.font_family_generic = attrs.getValue('style:font-family-generic')
                return
            if self.in_font_face:
                if name == 'svg:font-face-src':
                    self.in_font_face_src = True
                    return
                if self.in_font_face_src:
                    if name == 'svg:font-face-uri':
                        self.font_style = attrs.getValue('loext:font-style')
                        self.font_weight = attrs.getValue('loext:font-weight')
                        return
                    elif name == 'office:binary-data':
                        self.in_binary_data = True
                        return

    def write_font_data_to_file(self):
        assert self.font_name is not None
        assert self.font_family is not None
        #assert self.font_family_generic is not None
        assert self.font_style is not None
        assert self.font_weight is not None
        filename = f"{self.font_name}_{self.font_family}_{self.font_style}_{self.font_weight}"
        filename = re.sub(r"[^a-zA-Z0-9_]", "_", filename)
        filename = re.sub(r"_+", "_", filename)
        filename = filename.lower()
        filename = f"{filename}.ttf"
        filename = self.save_dir / filename
         # Remove whitespace characters from the base64 string
        clean_base64_data = self.font_data.getvalue().translate(
            str.maketrans('', '', ' \n\t\r')
        )
        logging.info(f"Writing font data to {filename}.")
        with open(filename, "wb") as f:
            f.write(base64.b64decode(clean_base64_data))


class ExtractFonts:
    def __init__(self, source_file, save_dir):
        self.source_file = Path(source_file)
        self.save_dir = Path(save_dir)
        if not self.save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)

    def extract(self):
        logging.info(f"Extracting fonts from {self.source_file}.")
        parser = xml.sax.make_parser()
        handler = FontHandler(self.save_dir)
        parser.setContentHandler(handler)
        try:
            logging.info(f"Parsing {self.source_file}.")
            parser.parse(self.source_file)
        except HandlerDoneException as e:
            pass
        logging.info(f"Done extracting fonts.")


# fodt-extract-fonts --sourcefile=<fodt-file> --savedir=<save-dir>
# -------------------------------------------------------------------
# SHELL USAGE:
#   fodt-extract-fonts --sourcefile=<fodt-file> --savedir=<save-dir>
#
# DESCRIPTION:
#
#  Extracts the font declarations from the fodt-file and saves them to the
#  save-dir.
#
@click.command()
@click.option('--sourcefile', type=str, required=True, help='Name of the fodt file.')
@click.option('--savedir', type=str, required=True, help='Name of the directory to save the font declarations.')
def extract_fonts(sourcefile: str, savedir: str) -> None:
    logging.basicConfig(level=logging.INFO)
    ExtractFonts(sourcefile, savedir).extract()

if __name__ == "__main__":
    extract_fonts()
