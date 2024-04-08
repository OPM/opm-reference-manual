import logging
import shutil
import click

from pathlib import Path
import fodt.string_functions
from fodt.constants import ClickOptions, Directories, FileNames, FileExtensions
from fodt.create_subdocument import CreateSubDocument2
from fodt.extract_subsections import ExtractSubSections
from fodt.helpers import Helpers
from fodt.remove_subsections import RemoveSubSections

class Splitter():
    def __init__(self, maindir: str, keyword_dir: str, chapter: int, section: int) -> None:
        self.chapter = chapter
        self.section = section
        self.maindir = Helpers.get_maindir(maindir)
        self.keyword_dir = Helpers.get_keyword_dir(keyword_dir, self.maindir)
        self.metadata_dir = self.maindir / Directories.meta
        assert self.maindir.is_dir()

    def create_backup_main_document(self) -> None:
        self.source_file = Helpers.create_backup_document(self.filename)

    def create_main_document(self) -> None:
        logging.info(f"Creating main document in {self.outputdir}.")
        self.destfile = self.outputdir / self.filename.name
        self.create_backup_main_document()
        replace_callback = Helpers.replace_section_callback
        remover = RemoveSubSections(
            self.source_file,
            self.destfile,
            self.keyword_dir,
            self.chapter,
            self.section,
            replace_callback
        )

    def create_subdocuments(self) -> None:
        logging.info(f"Creating subdocuments in {self.outputdir}.")
        creator = CreateSubDocument2(self.maindir, self.chapter, self.section)

    def extract_subsections(self) -> None:
        dir_ = self.maindir / Directories.chapters
        assert dir_.is_dir()
        filename = f"{self.chapter}.{FileExtensions.fodt}"
        self.filename = dir_ / filename
        assert self.filename.is_file()
        self.outputdir = dir_
        logging.info(f"Extracting subsections to {self.outputdir}.")
        extracter = ExtractSubSections(
            self.outputdir, self.filename, self.chapter, self.section
        )

    def split(self) -> None:
        self.extract_subsections()
        self.create_subdocuments()
        self.create_main_document()

# fodt-split-subdocument
# ----------------------
# SHELL USAGE:
#   fodt-split-subdocument --maindir=<main_dir> \
#                          --chapter=<chapter_number> \
#                          --section=<section_number>
# DESCRIPTION:
#
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.keyword_dir
@click.option('--chapter', type=int, required=True, help='Number of the chapter to split.')
@click.option('--section', type=int, required=True,
               help='Number of the section within the chapter to split.')
def split_subdocument(maindir: str, keyword_dir: str, chapter: int, section: int) -> None:
    logging.basicConfig(level=logging.INFO)
    splitter = Splitter(maindir, keyword_dir, chapter, section)
    splitter.split()

if __name__ == "__main__":
    split_subdocument()