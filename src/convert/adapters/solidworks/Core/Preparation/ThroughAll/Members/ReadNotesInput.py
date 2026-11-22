from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import (
    ReadMemberTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the actual head and partner links must prove a note pair before its captions become constructor inputs
def ReadNotesInput(NodesValue: tuple[ArchiveNode, ...]) -> NotesInput:
    if len(NodesValue) != 2:
        raise ValueError("source note owner requires one empty head and end pair")
    HeadValue, EndValue = NodesValue
    for NodeValue, PartnerValue, MarkerValue in (
        (HeadValue, EndValue, 1),
        (EndValue, HeadValue, 0),
    ):
        _ = RequireNative(NodeValue, "moNotesAreaFtrFolder_c")
        Values = NodeValue.FieldsValue
        if (
            Values.get("f388") is not PartnerValue
            or FieldInt(Values, "f37c") != MarkerValue
        ):
            raise ValueError(
                "source notes lack actual reciprocal head and end identity"
            )
        if any(
            FieldInt(Values, NameValue) != Expected
            for NameValue, Expected in (
                ("f0c", 0),
                ("f360", 1),
                ("f370", 0),
                ("f378", 1),
                ("f394", 0),
                ("f39c", 1),
            )
        ) or Values.get("f60") != {"list": {"n": 0, "items": []}, "tail": 0}:
            raise ValueError(
                "source note pair has unrepresented contents or folder state"
            )
    return NotesInput(
        ReadNodeName(HeadValue),
        ReadNodeName(EndValue),
        ReadMemberTime(HeadValue),
        ReadMemberTime(EndValue),
    )
