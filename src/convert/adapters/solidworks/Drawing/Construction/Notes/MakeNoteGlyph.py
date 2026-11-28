from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# an ordinary text token owns one utf sixteen code unit and its source position while native rendering computes glyph metrics
def MakeNoteGlyph(CodeValue: int, IndexValue: int) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moTextDataChar_c", 1),
        {
            "f08": IndexValue,
            "f0c": IndexValue,
            "f10": 0,
            "f20": {"f00": 0.0, "f04": 0.0, "f08": 0.0},
            "f2c": 0.0,
            "f30": 1,
            "f34": 0,
            "f38": 0.0,
            "f40": CodeValue,
        },
    )
