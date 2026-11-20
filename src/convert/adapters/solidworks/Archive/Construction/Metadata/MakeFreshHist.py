from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import (
    HistoryInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh version history preserves explicit originating provenance while computing its actual state and date code collections
def MakeFreshHist(InputValue: HistoryInput) -> ArchiveNode:
    if type(InputValue) is not HistoryInput:
        raise TypeError("fresh history requires validated explicit provenance")
    StampValue = {
        "f08": 0,
        "f0c": 0,
        "f10": 0,
        "f18": InputValue.CreatedAt,
        "f20": InputValue.CommentText,
    }
    CodesValue = [{"st": {"f08": InputValue.BuildCode}}]
    CodeHistory = ArchiveNode(
        RuntimeClass("moDateCodeHistory_c", 1),
        {"n": len(CodesValue), "states": CodesValue},
    )
    StatesValue = [{"st": {"f08": StampValue, "f30": 19000, "f38": CodeHistory}}]
    return ArchiveNode(
        RuntimeClass("moVersionHistory_c", 1),
        {
            "n": len(StatesValue),
            "states": StatesValue,
            "f28": 0,
            "f2c": 0xFFFFFFFF,
            "f30": InputValue.LicenseOrigin,
            "f38": InputValue.LanguageId,
            "f3c": int(InputValue.CjkSaved),
            "f40": 0,
        },
    )
