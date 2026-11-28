from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# ordinary note state derives its flag words and initializes the independent attachment and favorite branches
def MakeNoteTail(StyleValue: Mapping[str, object]) -> dict[str, object]:
    BitsValue = (1 << 0) | (1 << 20) | (1 << 27) | (1 << 28) | (1 << 29)
    WordsValue = ({"v": BitsValue >> 32}, {"v": BitsValue & ((1 << 32) - 1)})
    return {
        "f644": 1,
        "f648": int(StyleValue["f24"] == 1),
        "f64c": 0,
        "f628": MakePoint(),
        "f630": 0.0,
        "f690": StyleValue["f5c"],
        "f694": StyleValue["f58"],
        "f6a0": None,
        "f658": "",
        "f660": "",
        "f668": "",
        "f6b8": None,
        "f590": None,
        "f768": WordsValue,
        "n768": len(WordsValue),
        "f5a0": None,
        "f698": StyleValue["f68"],
        "f6d8": "",
        "f6e0": ArchiveNode(
            RuntimeClass("moFavoriteHandle_c", 1), {"f08": 2, "f0c": -1, "f10": 0}
        ),
        "f640": 0,
        "f5b0": None,
        "f5b8": 0,
        "f5bc": 0,
        "f710": StyleValue["f70"],
        "f5c0": 0,
        "f770": 0,
        "f784": -1,
        "f788": -1,
        "f78c": -1,
        "f790": None,
        "f6c0": None,
    }
