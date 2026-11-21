from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawFile import (
    LinkedDrawFile,
)
from convert.adapters.solidworks.Drawing.Construction.Profiles.MakeOriginChain import (
    MakeOriginChain,
)
from convert.adapters.solidworks.Drawing.Construction.Profiles.RequireOriginChild import (
    NeedOriginChild,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)


# component profile selection must derive both persistent identity and creation time from the same actual child origin
def MakeOriginProf(Candidate: LinkedDrawFile) -> ArchiveNode:
    ProfileValue = NeedOriginChild(Candidate.ChildValue)
    Reference = NeedProfileNode(
        Candidate.ViewValue.FieldsValue.get("f5d8"), "moReferenceInternal_c"
    )
    ChainValue = MakeOriginChain(Candidate.ModelGraph.ModelValue, Reference)
    FieldsValue = CompRefFields(ChainValue)
    OriginId = FieldInt(ProfileValue.FieldsValue, "f08")
    FieldsValue["ff0"] = {
        "f00": OriginId,
        "f08": DatumTime(Candidate.ChildValue.HeaderValue, OriginId),
    }
    return ArchiveNode(RuntimeClass("moCompProfile_c", 1), FieldsValue)
