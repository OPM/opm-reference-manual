import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

from fodt.constants import AutomaticStyles, Directories, FileNames, FileExtensions
from fodt.exceptions import HandlerDoneException, InputException, ParsingException
from fodt import helpers
from fodt import xml_helpers

class PartsHandler(xml.sax.handler.ContentHandler):
    def __init__(self, outputdir: Path, chapter: int, section: int,
                 predefined_keywords: list[str] | None
    ) -> None:
        self.outputdir = outputdir
        self.section = section
        self.chapter = chapter
        self.predefined_keywords = predefined_keywords
        self.current_section = 0
        self.current_subsection = 0
        self.styles = set()
        self.subsection = None
        self.in_subsection = False
        self.style_attrs = AutomaticStyles.attr_names
        self.in_bookmark = False
        self.save_keyword_name = False
        self.keyword_name = None
        self.keywords = []

    def add_section_start(
        self,
        name:str,
        attrs: xml.sax.xmlreader.AttributesImpl,
    ) -> None:
        self.subsection.write(xml_helpers.starttag(name, attrs))

    def characters(self, content: str):
        if self.save_keyword_name:
            # TODO: This extraction of keywords from the xml does not currently
            #  work since the keyword string may have interleaved <span> tags.
            #  This means that to extract the keyword we would have to build it
            #  up gradually from consecutive calls to this "characters()" method.
            # Since extracting the keyword names is a one time operation it was
            # decided to not spend time on this now and do the extraction manually
            # instead.
            #
            # Some contents are split by <span> tags, so we might not get the
            # expected space after the keyword name. Instead we get the end of string.
            if self.predefined_keywords is None:
                match = re.match(r'(\S+)(?:\s+|$)', content)
                if match is not None:
                    self.keyword_name = match.group(1)
                else:
                    ## See GRUPNET in the xml file 12.3.113 for an example of this.
                    self.keyword_name = "GRUPNET"
            else:
                self.keyword_name = self.predefined_keywords[self.current_subsection - 1]
            self.save_keyword_name = False
        if self.in_subsection:
            self.subsection.write(xml_helpers.escape(content))

    def collect_styles(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        for (key, value) in attrs.items():
            if key in self.style_attrs:
                self.styles.add(value)

    def endElement(self, name: str):
        if name == "text:section":
            if self.subsection is not None:
                self.write_to_file()
            raise HandlerDoneException(f"Done extracting sub sections.")
        elif self.in_bookmark and name == "text:bookmark-start":
            self.in_bookmark = False
            self.save_keyword_name = True
        if self.in_subsection:
            self.subsection.write(xml_helpers.endtag(name))

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        done = False
        write_subsection = False
        new_subsection = False
        if name == "text:h":
            if "text:outline-level" in attrs.getNames():
                level = attrs.getValue("text:outline-level")
                if level == "2":
                    if self.in_subsection:
                        done = True
                        write_subsection = True
                    else:
                        self.current_section += 1
                elif level == "3":
                    if self.in_subsection:
                        write_subsection = True
                        new_subsection = True
                    else:
                        if self.current_section == self.section:
                            self.in_subsection = True
                            new_subsection = True
        elif self.in_subsection and name == "text:bookmark-start":
            # Assume there always will be a text:bookmark-start tag immediately
            # following the text:h tag. This element will contain the keyword name
            # which we want to extract
            if self.keyword_name is None:
                text_name = attrs.getValue("text:name")
                if text_name.startswith("__RefHeading__"):
                    self.in_bookmark = True
        if write_subsection:
            self.write_to_file()
        if done:
            raise HandlerDoneException(f"Done extracting sub sections.")
        if new_subsection:
            self.current_subsection += 1
            self.subsection = io.StringIO()
            self.styles = set()
        if self.in_subsection:
            self.add_section_start(name, attrs)
            self.collect_styles(attrs)

    def write_keyword_order_file(self) -> None:
        """This method should be called after parsing the file is done. Then self.keywords
        will contain the keywords in the order they were found in the file."""
        directory = f"{self.chapter}.{self.section}"
        filename = FileNames.keywords
        dir_ = self.outputdir / Directories.info / Directories.keywords / directory
        dir_.mkdir(parents=True, exist_ok=True)
        file = dir_ / filename
        if not file.exists():
            with open(file, "w", encoding='utf8') as f:
                for keyword in self.keywords:
                    f.write(f"{keyword}\n")

    def write_subsection_to_file(self):
        directory = f"{self.chapter}.{self.section}"
        filename = f"{self.keyword_name}.{FileExtensions.xml}"
        self.keywords.append(self.keyword_name)
        dir_ = self.outputdir / Directories.info / Directories.subsections / directory
        dir_.mkdir(parents=True, exist_ok=True)
        path = dir_ / filename
        if path.exists():
            logging.info(f"Subsection {directory}:{self.keyword_name} :"
                         f"File {filename} already exists, skipping.")
            return
        with open(path, "w", encoding='utf8') as f:
            f.write(self.subsection.getvalue())
        self.subsection = None
        logging.info(f"Wrote subsection to file {filename}.")

    def write_styles_to_file(self) -> None:
        filename = f"{self.keyword_name}.{FileExtensions.txt}"
        directory = f"{self.chapter}.{self.section}"
        dir_ = self.outputdir / Directories.info / Directories.styles / directory
        dir_.mkdir(parents=True, exist_ok=True)
        path = dir_ / filename
        if path.exists():
            logging.info(f"Style file for {self.keyword_name} : File {filename} already exists, skipping.")
            return
        with open(path, "w", encoding='utf8') as f:
            for style in sorted(self.styles):
                f.write(f"{style}\n")
        self.styles = None
        logging.info(f"Wrote styles to file {filename}.")

    def write_to_file(self):
        self.write_subsection_to_file()
        self.write_styles_to_file()
        self.keyword_name = None # clear this until we find a new one

class ExtractSubSections():
    def __init__(
        self,
        outputdir: Path,
        filename: str,
        chapter: int,
        section: int,
    ) -> None:
        parser = xml.sax.make_parser()
        keyword_file = helpers.keyword_file(outputdir, chapter, section)
        predefined_keywords = None
        if keyword_file.exists():
            predefined_keywords = helpers.read_keyword_order(outputdir, chapter, section)
        handler = PartsHandler(outputdir, chapter, section, predefined_keywords)
        parser.setContentHandler(handler)
        try:
            parser.parse(filename)
        except HandlerDoneException as e:
            pass
        if predefined_keywords is None:
            handler.write_keyword_order_file()
        logging.info(f"Done extracting subsection parts.")
