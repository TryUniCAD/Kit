from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import (
    MakeFileConfig,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawFile import (
    LinkedDrawFile,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckFrontRefs import (
    CheckFrontRefs,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)


# equal names cannot substitute for the actual generated child file configuration and external reference aliases
def CheckOriginLink(Candidate: LinkedDrawFile) -> None:
    OwnerValue = NeedProfileNode(Candidate.ModelGraph.ModelValue, "moDrawing_c")
    ViewValue = NeedProfileNode(Candidate.ViewValue, "moAbsoluteView")
    Reference = NeedProfileNode(
        ViewValue.FieldsValue.get("f5d8"), "moReferenceInternal_c"
    )
    CheckFrontRefs(ViewValue, OwnerValue)
    EntryValue = NeedProfileNode(Reference.FieldsValue.get("f3b0"), "moExtObject_c")
    ChildValue = Candidate.ChildValue
    ChildFile = NeedProfileNode(
        ChildValue.HeaderValue.FieldsValue.get("f38"), "moExtObject_c"
    )
    if (
        ViewValue.FieldsValue.get("owner")
        is not Candidate.ModelGraph.SheetValue.SheetValue
        or Reference.FieldsValue.get("f3c0")
        != MakeFileConfig(ChildValue.SystemValue.RootValue, ChildValue.CurrentConfig)
        or RequireRecord(EntryValue.FieldsValue.get("shared")).get("h18")
        is not RequireRecord(ChildFile.FieldsValue.get("shared")).get("h18")
        or FieldInt(EntryValue.FieldsValue, "f70")
        != FieldInt(ChildValue.ManagerHeader.FieldsValue, "f60")
    ):
        raise ValueError(
            "origin display lost its actual generated child file or configuration"
        )
