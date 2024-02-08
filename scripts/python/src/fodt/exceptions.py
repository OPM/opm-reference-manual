class HandlerDoneException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Sax xml parsing finshed: {self.value}"

class InputException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Bad input: {self.value}"

class ParsingException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Parsing error: {self.value}"
