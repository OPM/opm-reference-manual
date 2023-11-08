import click

class AutomaticStyles():
    attr_names = {"text:style-name", "table:style-name", "draw:style-name", "style:name"}

class ClickOptions():
    filename = lambda func: click.option(
        '--filename',
        envvar='FODT_FILENAME',
        required=True,
        help='Name of the FODT file to extract from.'
    )(func)
    maindir = lambda func: click.option(
        '--maindir',
        envvar='FODT_MAIN_DIR',
        required=True,
        type=str,
        help='Directory to save generated files.'
    )(func)

class Directories():
    backup = "backup"
    info = "info"
    keywords = "keywords"
    meta = "meta"
    meta_sections = "sections"
    styles = "styles"
    chapters = "chapters"
    subsections = "subsections"

class FileExtensions():
    xml = "xml"
    fodt = "fodt"
    txt = "txt"

class FileNames():
    keywords = "keywords.txt"
    main_document = "main.fodt"
    office_attr_fn = "office_attrs.txt"
    styles = "styles"
    subsection = "section"
    subdocument = "section"

class MetaSections():
    names = [
        'office:meta',
        'office:settings',
        'office:scripts',
        'office:font-face-decls',
        'office:styles',
        'office:automatic-styles',
        'office:master-styles',
    ]

class TagEvent():
    NONE = 0
    START = 1
    END = 2

