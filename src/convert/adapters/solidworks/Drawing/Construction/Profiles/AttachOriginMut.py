from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawFile import (
    LinkedDrawFile,
)
from convert.adapters.solidworks.Drawing.Construction.Profiles.CheckOriginLink import (
    CheckOriginLink,
)
from convert.adapters.solidworks.Drawing.Construction.Profiles.AllocateOriginIdMut import (
    AllocateOriginIdMut,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Construction.Profiles.MakeOriginDisplay import (
    MakeOriginDisplay,
)
from convert.adapters.solidworks.Drawing.Construction.Profiles.MakeOriginProfile import (
    MakeOriginProfile,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import (
    WalkDrawNodes,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileList import (
    NeedProfileList,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)


# publication must append one actual origin display without replacing existing annotation or display state
def AttachOriginMut(Candidate: LinkedDrawFile) -> ArchiveNode:
    CheckOriginLink(Candidate)
    FolderValue = NeedProfileNode(
        Candidate.ViewValue.FieldsValue.get("f630"), "moDetailFolder_c"
    )
    if (
        FieldInt(Candidate.ModelGraph.ModelValue.FieldsValue, "fd44") != 10
        or NeedProfileList(FolderValue.FieldsValue.get("f8f8"))
        or any(
            NodeValue.ClassValue.NameValue.startswith("moDisplay")
            for NodeValue in WalkDrawNodes(Candidate.UiGraph.DocumentValue)
        )
    ):
        raise ValueError(
            "origin display requires a fresh drawing with no previous display allocations"
        )
    Reference = MakeOriginProfile(Candidate)
    DisplayValue = MakeOriginDisplay(FolderValue, Candidate.ViewValue, Reference)
    _ = AllocateOriginIdMut(Candidate.ModelGraph.ModelValue, DisplayValue)
    FolderValue.FieldsValue["f8f8"] = {"n": 1, "items": ({"o": DisplayValue},)}
    return DisplayValue
