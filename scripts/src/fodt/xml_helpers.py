import xml.sax.saxutils
from pathlib import Path

from fodt.constants import FileNames

class XMLHelper(object):
    header = """<?xml version="1.0" encoding="UTF-8"?>\n"""

    @staticmethod
    def endtag(name: str) -> str:
        return f"</{name}>"

    @staticmethod
    def get_office_document_start_tag(metadir: Path) -> None:
        fn = metadir / FileNames.office_attr_fn
        with open(fn, "r", encoding='utf-8') as f:
            attrs = f.read()
        attrs = attrs.replace("\n", " ")
        tag = "<office:document " + attrs + ">\n"
        return tag

    @staticmethod
    def starttag(name: str, attrs: dict[str, str], close_tag: bool = True) -> str:
        result = f"<{name}"
        for (key, value) in attrs.items():
            evalue = xml.sax.saxutils.escape(value)
            result += f" {key}=\"{evalue}\""
        if close_tag:
            result += ">"
        return result
