from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakePlacement import (
    MakePlacement,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
    RequireRecord,
)


# the selected occurrence must own the same actual child update configuration and rigid pose
def CheckCylPlace(
    Reference: ArchiveNode, FrameValue: PlaneFrame, ChildValue: PartCandidate
) -> None:
    FieldsValue = Reference.FieldsValue
    Selected = RequireRecord(FieldsValue.get("f3c0"))
    if (
        FieldsValue.get("f360") != MakePlacement(FrameValue)
        or FieldInt(FieldsValue, "f3e0")
        != FieldInt(ChildValue.HeaderValue.FieldsValue, "f40")
        or FieldInt(Selected, "f10")
        != FieldInt(ChildValue.CurrentConfig.FieldsValue, "f08")
        or Selected.get("f08") != ReadNodeName(ChildValue.CurrentConfig)
        or ReadFileKey(RequireNode(FieldsValue.get("f3b0"), "moExtObject_c"))
        != ReadFileKey(
            RequireNode(ChildValue.HeaderValue.FieldsValue.get("f38"), "moExtObject_c")
        )
    ):
        raise ValueError(
            "mate occurrence is outside the actual generated child and placement"
        )
