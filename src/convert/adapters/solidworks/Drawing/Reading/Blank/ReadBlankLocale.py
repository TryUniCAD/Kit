from convert.adapters.solidworks.Drawing.Reading.Blank.Fields import Fields
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require


# annotation selector effects must survive without inventing an unpersisted original style locale
def ReadBlankLocale(Value: object, HistoryLanguage: int) -> int:
    Annotation = Fields(Fields(Value)["f1f18"])
    Selectors = {
        Integer(Fields(Annotation[Key])["f1c"])
        for Key in (
            "f40",
            "fa0",
            "f108",
            "f178",
            "f1e8",
            "f250",
            "f2c0",
            "f398",
            "f418",
            "f4a0",
        )
    }
    Require(
        len(Selectors) == 1 and Selectors <= {0, 2},
        "blank annotation language effects differ",
    )
    Selector = Selectors.pop()
    if Selector == (2 if HistoryLanguage & 1023 == 13 else 0):
        return HistoryLanguage
    return 13 if Selector == 2 else 0
