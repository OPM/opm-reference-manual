import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
# from pathlib import Path

import click

from fodt.constants import ClickOptions
from fodt.exceptions import HandlerDoneException
from fodt.helpers import Helpers
from fodt.xml_handlers import GetUsedStylesHandler

class GetDefinedStylesHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        self.styles = {
            'font-face-decls': set(),
            'styles': set(),
            'automatic-styles': set(),
            'master-styles': set()
        }
        self.tag_names = set(self.styles.keys())
        self.current_tag_name = None
        self.in_section = False

    def endElement(self, name: str):
        if self.current_tag_name is None:
            return
        current_tag = f"office:{self.current_tag_name}"
        if name == current_tag:
            self.in_section = False
            self.tag_names.remove(self.current_tag_name)
            self.current_tag_name = None
            if len(self.tag_names) == 0:
                raise HandlerDoneException("Done parsing.")

    def get_styles(self) -> dict[str, set]:
        return self.styles

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if name.startswith("office:"):
            tag_name = name.removeprefix("office:")
            if tag_name in self.tag_names:
                self.current_tag_name = tag_name
                self.in_section = True
                return
        if self.in_section:
            for (key, value) in attrs.items():
                if key == "style:name":
                    self.styles[self.current_tag_name].add(value)
                    return


class GetDefinedStyles:
    def __init__(self, filename: str) -> set[str]:
        self.filename = filename
        self.styles = set()
        parser = xml.sax.make_parser()
        self.handler = GetDefinedStylesHandler()
        parser.setContentHandler(self.handler)
        try:
            parser.parse(filename)
        except HandlerDoneException as e:
            pass

    def get(self) -> set[str]:
        return self.handler.get_styles()


class GetUsedStyles:
    def __init__(self, filename: str) -> set[str]:
        self.filename = filename
        self.styles = set()
        parser = xml.sax.make_parser()
        self.handler = GetUsedStylesHandler()
        parser.setContentHandler(self.handler)
        parser.parse(filename)

    def get_style_attrs(self) -> dict[str, set]:
        return self.handler.get_style_attrs()

    def get_style_names(self) -> dict[str, set]:
        return self.handler.get_style_names()


class Validator:
    def __init__(self, filename) -> None:
        self.filename = filename

    def validate(self) -> None:
        defined_styles = self.get_defined_styles()
        #import pprint
        #pprint.pprint(defined_styles)
        used = self.get_used_styles()
        used_attrs = used.get_style_attrs()
        used_names = used.get_style_names()
        # pprint.pprint(used_names)
        self.check_styles(defined_styles, used_attrs, used_names)

    def check_styles(
        self,
        defined_styles: dict[str, set],
        used_attrs: dict[str, set],
        used_names: dict[str, set]
    ) -> None:
        for (style_name, tag_attrs) in used_attrs.items():
            found = False
            for section in defined_styles:
                if style_name in defined_styles[section]:
                    found = True
            if not found:
                tag_names = used_names[style_name]
                logging.info(f"Style {style_name} defined in tag {tag_names}, "
                             f"and tag attributes {tag_attrs} "
                             f"but not defined in any section.")

    def get_defined_styles(self) -> dict[str, set]:
        """Returns a set of all styles defined in the automatic-styles section
        in the document."""
        return GetDefinedStyles(self.filename).get()

    def get_used_styles(self) -> GetUsedStyles:
        """Returns a set of all styles used in the document."""
        return GetUsedStyles(self.filename)


# fodt-validate-document
# ----------------------
# SHELL USAGE:
#   fodt-validate-document --maindir=out subsection 4.3 ECHO
#   fodt-validate-document --maindir=out chapter 4
#
# DESCRIPTION:
#
# Checks if the document uses automatic styles that are not defined in the
# automatic styles section.
#

@click.group()
@ClickOptions.maindir
@click.option("--quiet", "-q", is_flag=True, help="Turn off verbose output")
@click.pass_context
def validate(ctx: click.Context, maindir: str, quiet: bool) -> None:
    """Checks if the document uses automatic styles that are not defined in the
    automatic styles section.
    """
    ctx.ensure_object(dict)
    ctx.obj["QUIET"] = quiet
    if quiet:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO)
    ctx.obj["MAIN_DIR"] = maindir

@validate.command()
@click.argument("section", type=str, required=True)
@click.argument("keyword", type=str, required=True)
@click.pass_context
def subsection(ctx: click.Context, section: str, keyword: str) -> None:
    (chapter, section) = Helpers.split_section(section)
    maindir = ctx.obj["MAIN_DIR"]
    filename = Helpers.keyword_fodt_file_path(maindir, chapter, section, keyword)
    Validator(filename).validate()


@validate.command()
@click.argument("chapter", type=str, required=True)
@click.pass_context
def chapter(ctx: click.Context, chapter: str) -> None:
    maindir = ctx.obj["MAIN_DIR"]
    filename = Helpers.chapter_fodt_file_path(maindir, chapter)
    Validator(filename).validate()


if __name__ == "__main__":
    validate()
