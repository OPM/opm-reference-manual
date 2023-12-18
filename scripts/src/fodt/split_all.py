import logging
import shutil
import subprocess
import tempfile
import click

from pathlib import Path
import fodt.string_functions
from fodt.constants import ClickOptions, Directories, FileNames
from fodt.remove_chapters import RemoveChapters

class Splitter():
    def __init__(
        self,
        maindir: str,
        filename: str,
        fontdir: str | None,
        keyword_dir: str | None,
    ) -> None:
        self.filename = filename
        self.fontdir = fontdir
        self.keyword_dir = keyword_dir
        self.maindir = Path(maindir)
        if self.maindir.exists():
            raise FileExistsError(f"Directory {self.maindir} already exists.")
        if self.keyword_dir is None:
            try_path = Path('../keyword-names')
            if try_path.exists():
                self.keyword_dir = try_path
            else:
                raise FileNotFoundError(f"Keyword names directory not found.")
        # TODO: Create a script that can create the font decls directory
        #       currently, you have to create it manually by running:
        #
        #  fodt-extract-metadata --maindir=temp --filename=original.fodt
        #
        #  and then copying the font-face-decls.xml file to the font-decls inside the
        #  self.fontdir directory.
        #
        if self.fontdir is None:
            try_path = Path('fonts')
            if try_path.exists():
                self.fontdir = try_path
            else:
                logging.info(
                     f"Font decls directory not specified. To reduce the size of the "
                     f"subdocuments, you should specify a directory containing the font "
                     f"declarations with the --font-decl-dir option. The full font "
                     f"declarations will be included in the main document, but not in the "
                     f"not in the subdocuments."
                )
                raise FileNotFoundError(f"Font decls directory not specified.")
        self.font_decl_dir = Path(self.fontdir) / 'font-face-decls'
        if not self.font_decl_dir.exists():
            raise FileNotFoundError(f"Font decls directory {self.font_decl_dir} not found.")
        self.maindir.mkdir(parents=True, exist_ok=True)
        self.chapters = "1-12"

    def copy_keyword_names(self) -> None:
        if self.keyword_dir is None:
            return
        logging.info(f"Copying keyword names from {self.keyword_dir}.")
        src = Path(self.keyword_dir)
        dest = (self.maindir / Directories.chapters / Directories.info
                / Directories.keywords)
        if not dest.exists():
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest, dirs_exist_ok=True)

    def run_split_main(self) -> None:
        logging.info(f"Running fodt-split-main with output to directory {self.maindir}.")
        subprocess.run([
            "fodt-split-main",
            f"--maindir={self.maindir}",
            f"--filename={self.filename}",
        ])

    def run_split_subdocuments(self) -> None:
        logging.info(f"Running fodt-split-subdocument with output to directory {self.maindir}.")
        sections = ["4.3", "5.3", "6.3", "7.3", "8.3", "9.3", "10.3", "11.3", "12.3"]
        for _ in sections:
            chapter, section = _.split('.')
            logging.info(f"Running fodt-split-subdocument section {_}.")
            subprocess.run([
                "fodt-split-subdocument",
                f"--maindir={self.maindir}",
                f"--chapter={chapter}",
                f"--section={section}"
            ])

    def set_font_decls_minimal(self) -> None:
        logging.info(f"Creating temporary file with minimal font face decls.")
        self.tempdir = tempfile.TemporaryDirectory()
        savename = Path(self.tempdir.name) / FileNames.main_document

        logging.info(f"Saving tempfile to {savename}..")
        font_decl_file = self.font_decl_dir / 'only-decl.xml'
        if not font_decl_file.exists():
            raise FileNotFoundError(f"Font decls file {font_decl_file} not found.")
        subprocess.run([
            "fodt-set-font-decls",
            f"--filename={self.filename}",
            f"--savename={savename}",
            f"--font-decl-file={font_decl_file}"
        ])
        self.filename = savename # Use tempfile name from now on

    def set_font_decls_include_all(self) -> None:
        mainfile = self.maindir / FileNames.main_document
        backupfile = f"{mainfile}.bak"
        shutil.move(mainfile, backupfile)
        savename = mainfile
        logging.info(f"Addding font-face-decls to {savename}..")
        font_decl_file = self.font_decl_dir / 'inc-fonts.xml'
        if not font_decl_file.exists():
            raise FileNotFoundError(f"Font decls file {font_decl_file} not found.")
        subprocess.run([
            "fodt-set-font-decls",
            f"--filename={backupfile}",
            f"--savename={savename}",
            f"--font-decl-file={font_decl_file}"
        ])
        self.filename = savename


    def split(self) -> None:
        self.copy_keyword_names()
        self.set_font_decls_minimal()
        self.run_split_main()
        self.run_split_subdocuments()
        self.set_font_decls_include_all()
        logging.info(f"Done.")

@click.command()
@ClickOptions.maindir()
@ClickOptions.filename
@click.option(
    '--font-decl-dir', type=str, required=False,
    help='Name of the directory containing the font declarations.'
)
@ClickOptions.keyword_dir
def split_all(
    maindir: str, filename: str, font_decl_dir: str | None, keyword_dir: str | None
) -> None:
    logging.basicConfig(level=logging.INFO)
    splitter = Splitter(maindir, filename, font_decl_dir, keyword_dir)
    splitter.split()

if __name__ == "__main__":
    split_all()