import xml.sax.saxutils
from pathlib import Path

from fodt.constants import FileNames

HEADER = """<?xml version="1.0" encoding="UTF-8"?>\n"""

# NOTE: xml.sax.saxutils.escape() escapes only the three characters
# "&", "<", ">". But LibreOffice also escapes the characters '"', "'" so
# we need to escape them as well in order to not get large PR diffs when
# modifying the .fodt files sometimes with a script and sometimes with
# LibreOffice.
ESCAPE_MAP = {'"': '&quot;', "'": '&apos;'}

def endtag(name: str) -> str:
    return f"</{name}>"

def escape(content: str) -> str:
    return xml.sax.saxutils.escape(content, ESCAPE_MAP)

def get_office_document_start_tag(metadir: Path) -> None:
    fn = metadir / FileNames.office_attr_fn
    with open(fn, "r", encoding='utf-8') as f:
        attrs = f.read()
    attrs = attrs.replace("\n", " ")
    tag = "<office:document " + attrs + ">\n"
    return tag

def starttag(name: str, attrs: dict[str, str], close_tag: bool = True) -> str:
    result = f"<{name}"
    for (key, value) in attrs.items():
        evalue = escape(value)
        result += f" {key}=\"{evalue}\""
    if close_tag:
        result += ">"
    return result
