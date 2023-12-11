import xml.sax.saxutils

class XMLHelper(object):
    header = """<?xml version="1.0" encoding="UTF-8"?>\n"""

    @staticmethod
    def endtag(name: str) -> str:
        return f"</{name}>"

    @staticmethod
    def starttag(name: str, attrs: dict[str, str]) -> str:
        result = f"<{name}"
        for (key, value) in attrs.items():
            evalue = xml.sax.saxutils.escape(value)
            result += f" {key}=\"{evalue}\""
        result += ">"
        return result
