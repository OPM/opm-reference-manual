import logging
import re

from pathlib import Path

from fodt.automatic_styles_filter import AutomaticStylesFilter2, AutomaticStylesFilter3
from fodt.constants import Directories, FileExtensions, FileNames, MetaSections
from fodt.exceptions import InputException
from fodt.helpers import Helpers
from fodt.xml_helpers import XMLHelper
from fodt.styles_filter import StylesFilter

class CreateSubDocument():
    def create_documents(self, parts: list[str]) -> None:
        outputdir = self.outputdir
        if not self.is_chapter:
            outputdir = outputdir / f"{self.chapter}.{self.section}"
        outputdir.mkdir(parents=True, exist_ok=True)
        for part in parts:
            outputfile: Path = outputdir / f"{part}.{FileExtensions.fodt}"
            if outputfile.exists():
                logging.info(f"Skipping {outputfile} because it already exists.")
                continue
            with open(outputfile, "w", encoding='utf-8') as f:
                self.outputfile = f
                self.write_xml_header()
                self.write_office_document_start_tag()
                self.write_meta(part)
                self.write_office_body_start_tag(part)
                self.write_section(part)
                self.write_xml_footer()
            logging.info(f"Created FODT subdocument {outputfile}")

    def create_subsection_template(self, part: str) -> str:
        template = Helpers.read_keyword_template()
        template = re.sub(r"###KEYWORD_NAME###", part, template)
        return template

    def write_office_body_start_tag(self, part: str) -> None:
        section_name = part
        if self.is_chapter:
            section_name = f"Chapter{part}"
        self.outputfile.write("\n <office:body>")
        self.outputfile.write(f"""
  <office:text text:use-soft-page-breaks="true">
   <office:forms form:automatic-focus="false" form:apply-design-mode="false"/>
   <text:sequence-decls>
    <text:sequence-decl text:display-outline-level="0" text:name="Illustration"/>
    <text:sequence-decl text:display-outline-level="1" text:separation-character="." text:name="Table"/>
    <text:sequence-decl text:display-outline-level="1" text:separation-character="." text:name="Text"/>
    <text:sequence-decl text:display-outline-level="0" text:name="Drawing"/>
    <text:sequence-decl text:display-outline-level="1" text:separation-character="." text:name="Figure"/>
    <text:sequence-decl text:display-outline-level="0" text:name="Listing"/>
   </text:sequence-decls>
   <text:user-field-decls>
    <text:user-field-decl office:value-type="string" office:string-value="" text:name="SEQ"/>
    <text:user-field-decl office:value-type="float" office:value="1" text:name="MD"/>
    <text:user-field-decl office:value-type="string" office:string-value="" text:name="SEQ CHAPTER \h \r 1"/>
   </text:user-field-decls>
   <text:p text:style-name="P18776"/>
   <text:section text:style-name="Sect1" text:name="{section_name}">
""")

    def write_office_document_start_tag(self) -> None:
        fn = self.metadir / FileNames.office_attr_fn
        with open(fn, "r", encoding='utf-8') as f:
            attrs = f.read()
        attrs = attrs.replace("\n", " ")
        self.outputfile.write("<office:document " + attrs + ">\n")

    def write_meta(self, part: str) -> None:
        section_names = MetaSections.names
        for section_name in section_names:
            section_name = section_name.removeprefix("office:")
            self.write_meta_section(section_name, part)

    def write_meta_section(self, section_name: str, part: str) -> None:
        section_file = self.metadir / Directories.meta_sections / f"{section_name}.{FileExtensions.xml}"
        with open(section_file, "r", encoding='utf-8') as f:
            content = f.read()
            if section_name == "automatic-styles":
                if self.add_keyword:
                    filter = AutomaticStylesFilter3(self.metadir, content, part)
                    pass
                else:
                    if self.is_chapter:
                        dir_ = self.stylesdir
                    else:
                        dir_ = self.stylesdir / f"{self.chapter}.{self.section}"
                    filter = AutomaticStylesFilter2(self.metadir, dir_, content, part)
                content = filter.get_filtered_content()
            elif section_name == "styles":
                if not self.is_chapter:
                    # The styles chapter numbering uses numerical subsection values,
                    #  so we need to convert the part to a numerical value.
                    subsection = self.keywords[part]
                    part = f"{self.chapter}.{self.section}.{subsection}"
                filter = StylesFilter(content, part)
                content = filter.get_filtered_content()
        self.outputfile.write(content)

    def write_section(self, part: str) -> None:
        if self.is_chapter:
            dir_ = self.extracted_sections_dir
        else:
            dir_ = self.extracted_sections_dir / f"{self.chapter}.{self.section}"
        section_file = dir_ / f"{part}.{FileExtensions.xml}"
        content = None
        if section_file.exists():
            with open(section_file, "r", encoding='utf-8') as f:
                content = f.read()
        else:
            if not self.is_chapter:
                content = self.create_subsection_template(part)
        if content is None:
            raise InputException(f"Could not find section file {section_file}")
        self.outputfile.write("\n")
        self.outputfile.write(content)

    def write_xml_footer(self) -> None:
        self.outputfile.write("""
   </text:section>
  </office:text>
 </office:body>
</office:document>
""")

    def write_xml_header(self) -> None:
        self.outputfile.write(XMLHelper.header)

class CreateSubDocument1(CreateSubDocument):
    def __init__(
        self,
        maindir:str,
        chapters: list[int],
    ) -> None:
        self.main_dir = Path(maindir)
        self.extracted_sections_dir = self.main_dir / Directories.info / Directories.chapters
        self.stylesdir = self.main_dir / Directories.info / Directories.styles
        self.metadir = self.main_dir / Directories.meta
        self.outputdir = self.main_dir / Directories.chapters
        self.is_chapter = True
        parts = [str(item) for item in chapters]
        self.add_keyword = False
        self.create_documents(parts)


class CreateSubDocument2(CreateSubDocument):
    def __init__(self, maindir: str, chapter: str, section: str) -> None:
        self.maindir = Path(maindir)
        self.chapter = chapter
        self.section = section
        self.metadir = self.maindir / Directories.meta
        self.documentdir = self.maindir / Directories.chapters
        self.extracted_sections_dir = self.documentdir / Directories.info / Directories.subsections
        self.stylesdir = self.documentdir / Directories.info / Directories.styles
        self.outputdir = self.documentdir / Directories.subsections
        self.is_chapter = False
        parts = self.get_parts()
        keyw_list = Helpers.read_keyword_order(self.documentdir, chapter, section)
        self.keywords = Helpers.keywords_inverse_map(keyw_list)
        self.add_keyword = False
        self.create_documents(parts)

    def get_parts(self) -> list[str]:
        dir_ = self.extracted_sections_dir / f"{self.chapter}.{self.section}"
        assert dir_.is_dir()
        files = dir_.glob(f"*.{FileExtensions.xml}")
        files = [str(item.name) for item in files]
        parts = [item.removesuffix(f".{FileExtensions.xml}") for item in files]
        return parts

class CreateSubDocument3(CreateSubDocument):
    def __init__(
            self, maindir: str, keyword_dir: str, chapter: str, section: str, keyword: str
    ) -> None:
        self.maindir = Path(maindir)
        self.keyword_dir = keyword_dir
        self.chapter = chapter
        self.section = section
        self.keyword = keyword
        self.metadir = self.maindir / Directories.meta
        self.documentdir = self.maindir / Directories.chapters
        self.extracted_sections_dir = self.documentdir / Directories.info / Directories.subsections
        self.stylesdir = self.documentdir / Directories.info / Directories.styles
        self.outputdir = self.documentdir / Directories.subsections
        self.is_chapter = False
        parts = [self.keyword]
        keyw_list = Helpers.read_keyword_order_v2(self.keyword_dir, chapter, section)
        self.keywords = Helpers.keywords_inverse_map(keyw_list)
        self.add_keyword = True
        self.create_documents(parts)
