import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions, Directories, FileExtensions, FileNames
from fodt.exceptions import HandlerDoneException
from fodt.xml_handlers import GetUsedStylesHandler


class GetAutoStylesHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        self.in_section = False
        self.current_tag_name = None
        self.styles = set()

    def endElement(self, name: str):
        if self.current_tag_name is None:
            return
        if name == self.current_tag_name:
            self.in_section = False
            self.current_tag_name = None
            raise HandlerDoneException("Done parsing.")

    def get_styles(self) -> dict[str, set]:
        return self.styles

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if name == "office:automatic-styles":
            self.current_tag_name = name
            self.in_section = True
            return
        if self.in_section:
            for (key, value) in attrs.items():
                if key == "style:name":
                    self.styles.add(value)
                    return



class ExtractAutoStyles:
    def __init__(self, maindir: str) -> set[str]:
        self.maindir = maindir
        self.styles = set()
        parser = xml.sax.make_parser()
        metadir = Path(self.maindir) / Directories.meta
        sections_dir = metadir / Directories.meta_sections
        section = 'automatic-styles'
        filename = sections_dir / f"{section}.{FileExtensions.xml}"
        self.handler = GetAutoStylesHandler()
        parser.setContentHandler(self.handler)
        try:
            parser.parse(filename)
        except HandlerDoneException as e:
            pass

    def get(self) -> set[str]:
        return self.handler.get_styles()


class ExtractOtherStyles:
    def __init__(self, maindir: str) -> set[str]:
        self.maindir = maindir
        parser = xml.sax.make_parser()
        metadir = Path(self.maindir) / Directories.meta
        sections_dir = metadir / Directories.meta_sections
        section_names = ['font-face-decls', 'styles', 'master-styles']
        self.style_attrs = {}
        self.style_names = {}
        for section in section_names:
            filename = sections_dir / f"{section}.{FileExtensions.xml}"
            handler = GetUsedStylesHandler()
            parser.setContentHandler(handler)
            try:
                parser.parse(filename)
            except HandlerDoneException as e:
                pass
            # TODO: we may need to copy this dict instead of referencing it if
            # for some reason the handler is reused.
            self.style_attrs[section] = handler.get_style_attrs()
            self.style_names[section] = handler.get_style_names()

    def get_style_attrs(self) -> dict[str, dict[str, set]]:
        return self.style_attrs

    def get_style_names(self) -> dict[str, dict[str, set]]:
        return self.style_names


class ExtractStyleInfo:
    def __init__(self, maindir: str) -> None:
        self.maindir = maindir

    def extract(self) -> None:
        auto_styles = self.extract_auto_styles()
        (other_style_names, other_style_attrs) = self.extract_other_styles()
        self.write_to_file(auto_styles, other_style_names, other_style_attrs)

    def extract_auto_styles(self) -> set[str]:
        auto_styles = ExtractAutoStyles(self.maindir).get()
        logging.info(f"Found {len(auto_styles)} automatic styles.")
        return auto_styles

    def extract_other_styles(self) -> dict[str, dict[str, set]]:
        extractor = ExtractOtherStyles(self.maindir)
        other_style_names = extractor.get_style_names()
        other_style_attrs = extractor.get_style_attrs()
        return (other_style_names, other_style_attrs)

    def write_to_file(
        self,
        auto_styles: set[str],
        other_style_names: dict[str, dict[str, set]],
        other_style_attrs: dict[str, dict[str, set]]
    ) -> None:
        outputdir = Path(self.maindir) / Directories.meta
        outputdir.mkdir(parents=True, exist_ok=True)
        filename = outputdir / FileNames.styles_info_fn
        if filename.exists():
            logging.info(f"Style info file {filename} already exists, skipping.")
            return
        sections = other_style_names.keys()
        styles = set()
        import pprint
        #pprint.pprint(auto_styles)
        for section in sections:
            section_style_names = other_style_names[section].keys()
            for style in section_style_names:
                if style in auto_styles:
                    styles.add(style)
        with open(filename, "w", encoding='utf-8') as f:
            for style in sorted(styles):
                f.write(f"{style}\n")
        logging.info(f"Wrote style info to {filename}.")

# fodt-extract-styleinfo
# ----------------------
# SHELL USAGE:
#   fodt-extract-style-info --maindir=<main_directory>
#
# DESCRIPTION:
#
# Extracts the styles used in meta sections font-face-decls, styles, and master-styles
# that are defined in meta section automatic-styles.
#
@click.command()
@ClickOptions.maindir
def extract_style_info(maindir: str) -> None:
    logging.basicConfig(level=logging.INFO)
    ExtractStyleInfo(maindir).extract()

if __name__ == "__main__":
    extract_style_info()
