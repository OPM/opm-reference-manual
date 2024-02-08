import logging
import sys

import click

import fodt.string_functions

from fodt.constants import ClickOptions
from fodt.create_subdocument import CreateSubDocument1
from fodt.extract_metadata import ExtractMetaData
from fodt.extract_xml_tag import ExtractXmlTag
from fodt.extract_chapters import ExtractChapterParts
from fodt.extract_tag_attrs import ExtractDocAttrs
from fodt.remove_elements import RemoveElements
from fodt.remove_chapters import RemoveChapters

# NOTE: str.removeprefix() requires python >= 3.9
# NOTE: type hints for collection of builtin types requires python>=3.9, see
#  https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
# NOTE: type hints using union types (using pipe only), e.g. "str | None",
#   requires python >= 3.10
#   see: https://docs.python.org/3/library/stdtypes.html#types-union
MIN_PYTHON = (3, 10)
if sys.version_info < MIN_PYTHON:  # pragma: no cover
    sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.")


## SHELL COMMANDS
#-----------------

# fodt-create-subdocuments
# -----------------------
# SHELL USAGE:
#   fodt-create-subdocuments --maindir=<main_dir> \
#                            --chapters=<chapter_numbers>
# NOTES:
#   Prepare the following files in advance:
#  - Use command fodt-extract-metadata to extract the metadata files.
#  - Use command fodt-extract-chapters to extract the chapter parts.
#  - Use command fodt-extract-document-attributes to extract the document attributes.
#
# DESCRIPTION:
#   Create a FODT subdocument file.
#   The following files inside "main_dir" are required:
#   - In the meta directory:
#     - office_attr.txt, containing the office:document tag's attributes
#     - Inside the sub directory "sections":
#       - meta.xml, containing the office:meta section
#       - settings.xml, containing the office:settings section
#       - scripts.xml, containing the office:scripts section
#       - font-face-decls.xml, containing the office:font-face-decls section
#       - styles.xml, containing the office:styles section
#       - automatic-styles.xml, containing the office:automatic-styles section
#       - master-styles.xml, containing the office:master-styles section
#   - In the "extracted_chapters" directory:
#     - chapter<chapter_number1>.xml, chapter<chapter_number2>.xml, ...
#        containing the chapter templates to use for the subdocuments
#
# EXAMPLE:
#
#   fodt-create-subdocuments --maindir=out --chapters=1,2
#
@click.command()
@ClickOptions.maindir()
@click.option('--chapters', required=True, type=str,
               help='Create sub documents for these chapter numbers.')
def create_subdocument(
    maindir: str,
    chapters: str,
) -> None:
    """Create a FODT chapter sub document."""
    logging.basicConfig(level=logging.INFO)
    chapters = fodt.string_functions.parse_parts(chapters)
    creator = CreateSubDocument1(maindir, chapters)

# fodt-extract-chapters
# --------------------------
# SHELL USAGE:
#   fodt-extract-chapters  --maindir=<main_dir> \
#                          --chapters=<chapter_numbers> \
#                          --filename=<fodt_input_file>
# DESCRIPTION:
#   Extract one or more "chapter" parts from a FODT file.
#   A "chapter" part is defined by two consecutive text:h tags with the same outline level (1)
#   in the body section of fodt file. The first tag is included in the part, the second is not.
#   The chapter parameter is a comma separated list of chapter numbers, e.g. "1,3,5, 7-10".
#   Chapter numbers start at 1 from the beginning of the file.
#
# The following files are created:
#   - chapter{chapter_number1}.xml, chapter{chapter_number2}.xml, ... containing the extracted chapters
#
@click.command()
@ClickOptions.maindir()
@click.option('--chapters', type=str, required=True, help='Parts to extract.')
@ClickOptions.filename
def extract_chapters(maindir: str, chapters: str, filename: str) -> None:
    """Extract one ore more "chapter" parts from a FODT file."""
    logging.basicConfig(level=logging.INFO)
    chapters = fodt.string_functions.parse_parts(chapters)
    extracter = ExtractChapterParts(maindir, filename, chapters)

# fodt-remove-elements
# --------------------
# SHELL USAGE:
#   fodt-remove-elements --element-name=<element_name> \
#                        --count=<number_of_elements> \
#                        --outputfn=<fodt_output_file> \
#                        --filename=<fodt_input_file>
# DESCRIPTION:
#   Remove one ore more elements from a FODT file. An element is defined by a start tag
#   and an end tag and the content between those.
#
@click.command()
@click.option('--element-name', required=True, type=str, help='Name of element to remove')
@click.option('--count', default=1, type=int, help='Number of elements to remove')
@click.option('--outputfn', required=True, help='Name of output file')
@ClickOptions.filename
def remove_elements(element_name: str, outputfn: str, count: str, filename: str) -> None:
    """Remove one ore more elements from a FODT file."""
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Removing {count} elements from {filename}.")
    remover = RemoveElements(element_name, outputfn, filename, count)

# fodt-remove-chapters
# --------------------
# SHELL USAGE:
#   fodt-remove-chapters --chapters=<chapter_numbers> \
#                        --outputfn=<fodt_output_file> \
#                        --filename=<fodt_input_file>
# DESCRIPTION:
#   Remove one or more "chapter" parts from a FODT file.
#   A "chapter" part is defined by two consecutive text:h tags with the same outline level (1)
#   in the body section of the fodt file.
#
# EXAMPLE:
#
#   fodt-remove-chapters --chapters=1-12 --outputfn=removed.fodt --filename=original.fodt
#
@click.command()
@click.option('--chapters', type=str, required=True, help='Chapters to remove')
@click.option('--outputfn', required=True, help='Name of output file')
@ClickOptions.filename
def remove_chapters(outputfn: str, chapters: str, filename: str) -> None:
    """Remove one ore more "chapters" from a FODT file."""
    logging.basicConfig(level=logging.INFO)
    chapters = fodt.string_functions.parse_parts(chapters)
    remover = RemoveChapters(outputfn, filename, chapters)

# fodt-extract-document-attributes
# --------------------------------
# SHELL USAGE:
#   fodt-extract-document-attributes --maindir=<main_dir> \
#                                    --filename=<fodt_input_file>
# DESCRIPTION:
#   Extract the office:document tag's attributes.
#   The following files are created inside "maindir":
#   - meta/office_attrs.txt, containing the office:document tag's attributes
#   This file is used by fodt-create-subdocuments to create a new fodt file.
#
# EXAMPLE:
#
#   fodt-extract-document-attributes --maindir=out --filename=original.fodt
#
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.filename
def extract_document_attributes(maindir: str, filename: str) -> None:
    """Extract the office:document tag's attributes."""
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Extracting document attributes from {filename}.")
    ExtractDocAttrs(maindir, filename)


# fodt-extract-metadata
# ---------------------
# SHELL USAGE:
#   fodt-extract-metadata --maindir=<main_dir> \
#                         --filename=<fodt_input_file>
# DESCRIPTION:
#   Extract the metadata from a fodt file and saves metadata files in subdirectory
#   "meta/sections" inside "maindir".
#   The following metadata files are created:
#   - meta.xml, containing the office:meta section
#   - settings.xml, containing the office:settings section
#   - scripts.xml, containing the office:scripts section
#   - font-face-decls.xml, containing the office:font-face-decls section
#   - styles.xml, containing the office:styles section
#   - automatic-styles.xml, containing the office:automatic-styles section
#   - master-styles.xml, containing the office:master-styles section
#
# EXAMPLE:
#
#   fodt-extract-metadata --maindir=out --filename=original.fodt
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.filename
def extract_metadata(maindir: str, filename: str) -> None:
    """Extract metadata from a FODT file."""
    logging.basicConfig(level=logging.INFO)
    extracter = ExtractMetaData(maindir, filename)

# fodt-extract-xml-tag
# --------------------
# SHELL USAGE:
#   fodt-extract-xml-tag --tag_name=<tag_name> \
#                        --filename=<fodt_input_file>
# DESCRIPTION:
#   Extract a section from a fodt file and prints it to stdout.
#   The tag_name is the name of the xml tag, e.g. "office:meta".
#   NOTE: this extracts a section as defined by an xml tag, whereas
#   command fodt-extract-special-parts extracts a section as defined
#   by two consecutive text:h tags with the same outline level.
@click.command()
@ClickOptions.filename
@click.option(
    '--section',
    required=True,
    help='Name of the tag to extract. Example: "office:meta"'
)
def extract_xml_tag(filename: str, section: str) -> None:
    """Extract an xml tag from the fodt file."""
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Extracting a section from {filename}.")
    extracter = ExtractXmlTag(filename, section)

def main():
    logging.basicConfig(level=logging.INFO)
    print("Hello, World!")

if __name__ == "__main__":  # pragma: no cover
    main()