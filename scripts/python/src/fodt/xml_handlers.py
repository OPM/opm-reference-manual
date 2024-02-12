import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

class GetUsedStylesHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        # The values of the dict below list the attribute-names where the style is used.
        self.style_attrs: dict[str, set] = dict()
        # The values of the dict below list the tag-names where the style is used.
        self.style_names: dict[str, set] = dict()

    def endElement(self, name: str):
        pass

    def get_style_attrs(self) -> dict[str, set]:
        return self.style_attrs

    def get_style_names(self) -> dict[str, set]:
        return self.style_names

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        for (key, value) in attrs.items():
            if value == "":
                continue
            if (key.endswith("page-name")       or key.endswith("display-name") or
                key.endswith("font-style-name") or key.endswith("font-name")):
                continue
            if key.endswith("style-name") or re.fullmatch(r"style:.*-name", key):
                if value in self.style_attrs:
                    self.style_attrs[value].add(key)
                else:
                    self.style_attrs[value] = {key}
                if key in self.style_names:
                    self.style_names[value].add(name)
                else:
                    self.style_names[value] = {name}

