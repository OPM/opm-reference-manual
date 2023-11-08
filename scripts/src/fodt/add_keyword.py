import logging
import click
from pathlib import Path
from fodt.constants import ClickOptions, Directories, FileExtensions
from fodt.create_subdocument import CreateSubDocument3
from fodt.helpers import Helpers
from fodt.remove_subsections import RemoveSubSections

class AddKeyword():
    def __init__(self, maindir: str, keyword: str, chapter: int, section: int) -> None:
        self.maindir = maindir
        self.keyword = keyword
        self.chapter = chapter
        self.section = section
        self.add_keyword()
        self.add_style_file()
        self.update_subdocument()
        self.update_chapter_document()

    def add_keyword(self) -> None:
        self.documentdir = Path(self.maindir) / Directories.chapters
        keyw_list = Helpers.read_keyword_order(self.documentdir, self.chapter, self.section)
        keywords = set(keyw_list)
        if self.keyword in keywords:
            logging.info(f"Keyword {self.keyword} already exists. Aborting.")
            return
        keywords.add(self.keyword)
        keyw_list = sorted(list(keywords))
        Helpers.write_keyword_order(self.documentdir, self.chapter, self.section, keyw_list)
        logging.info(f"Added keyword {self.keyword} to chapter {self.chapter}, section {self.section}.")
        return

    def add_style_file(self) -> None:
        filename = f"{self.keyword}.{FileExtensions.txt}"
        directory = f"{self.chapter}.{self.section}"
        dir_ = self.documentdir / Directories.info / Directories.styles / directory
        dir_.mkdir(parents=True, exist_ok=True)
        path = dir_ / filename
        if path.exists():
            logging.info(f"Style file for {self.keyword} : File {filename} already exists, skipping.")
            return
        # NOTE: These styles were taken from the COLUMNS keyword in section 4.3 since that keyword
        #       was also used for new the keyword template, see create_subsection_template() in
        #       src/fodt/create_subdocument.py
        styles = ['Internet_20_link', 'P18335', 'P18345', 'P6057', 'P6690', 'T1', 'Table990', 'Table990.1',
                  'Table990.A', 'Table990.A1', 'Table990.E', 'Table990.F', 'Table990.H1', '_40_TextBody']
        with open(path, "w", encoding='utf8') as f:
            for style in styles:
                f.write(f"{style}\n")
        logging.info(f"Wrote styles to file {filename}.")

    def update_chapter_document(self) -> None:
        logging.info(f"Updating chapter document {self.chapter}.")
        filename = self.documentdir / f"{self.chapter}.{FileExtensions.fodt}"
        source_file = Helpers.create_backup_document(filename)
        dest_file = filename
        replace_callback = Helpers.replace_section_callback
        remover = RemoveSubSections(
            source_file,
            dest_file,
            self.chapter,
            self.section,
            replace_callback
        )

    def update_subdocument(self) -> None:
        logging.info(f"Updating subdocument {self.chapter}.{self.section}:{self.keyword}.")
        creator = CreateSubDocument3(self.maindir, self.chapter, self.section, self.keyword)



# fodt-add-keyword
# -----------------
#
# SHELL USAGE:
#
# fodt-add-keyword --maindir=<main_dir> \
#                   --keyword=<keyword> \
#                   --chapter=<chapter_number> \
#                   --section=<section_number>
#
# DESCRIPTION:
#
# Adds a new keyword to the given chapter and section
#
@click.command()
@ClickOptions.maindir
@click.option('--keyword', type=str, required=True, help='Name of the keyword to add.')
@click.option('--chapter', type=int, required=True, help='Number of the chapter.')
@click.option('--section', type=int, required=True, help='Number of the section.')
def add_keyword(maindir: str, keyword: str, chapter: int, section: int) -> None:
    logging.basicConfig(level=logging.INFO)
    add_keyword = AddKeyword(maindir, keyword, chapter, section)

if __name__ == "__main__":
    add_keyword()