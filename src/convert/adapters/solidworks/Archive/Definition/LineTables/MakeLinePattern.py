from convert.adapters.solidworks.Archive.Definition.LineTables.LinePattern import (
    LinePattern,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh named style construction appends authored signed doubles and applies the optional thick thin setter
def MakeLinePattern(InputValue: LinePattern) -> ArchiveNode:
    if type(InputValue) is not LinePattern:
        raise TypeError("line pattern construction requires typed semantic input")
    Segments = [{"seg": Value} for Value in InputValue.SegmentsValue]
    return ArchiveNode(
        RuntimeClass("moLineStyle_c", 1),
        {
            "f08": InputValue.NameValue,
            "f10": InputValue.CaptionValue,
            "f18": Segments,
            "nseg": len(Segments),
            "f20": int(InputValue.ThickThinValue),
        },
    )
