from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldText
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Construction.References.DrawReferences import (
    DrawReferences,
)
from convert.adapters.solidworks.Drawing.Construction.References.MakeDrawEntry import (
    MakeDrawEntry,
)
from convert.adapters.solidworks.Drawing.Construction.References.MakeDrawExt import (
    MakeDrawExt,
)
from convert.adapters.solidworks.Drawing.Construction.References.MakeDrawRef import (
    MakeDrawRef,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.ProfileTime import (
    MakeProfileTime,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)


# one linked view installs its generated child directory before allocating the internal reference and separate component property owner
def MakeDrawRefsMut(
    GraphValue: DrawRootGraph,
    ChildValue: PartCandidate,
    BoundsValue: dict[str, float],
    BuildValue: DrawBuild,
) -> DrawReferences:
    OwnerValue = GraphValue.ModelValue
    HeaderValue = NeedConceptNode(OwnerValue.FieldsValue["fa8"], "moHeader_c")
    Manager = NeedConceptNode(OwnerValue.FieldsValue["f16a8"], "moDrwCompPropMgr_c")
    if (
        HeaderValue.FieldsValue["f30"] is not None
        or Manager.FieldsValue["n10"]
        or Manager.FieldsValue["f08"]
    ):
        raise ValueError(
            "drawing link construction requires the actual fresh empty reference directory"
        )
    EntryValue = MakeDrawEntry(ChildValue)
    NameValue = FieldText(
        NeedConceptNode(
            ChildValue.SystemValue.RootValue.FieldsValue["f18"], "moNodeName_c"
        ).FieldsValue,
        "f08",
    )
    Internal = MakeDrawRef(
        "moReferenceInternal_c",
        NameValue + "-1",
        OwnerValue,
        ChildValue,
        EntryValue,
        BuildValue.TargetValue,
        GraphValue.Allocator,
    )
    Internal.FieldsValue.update(
        {
            "f0c": 0,
            "has_f370": 1,
            "f370": dict(BoundsValue),
            **MakeProfileTime(BuildValue.CreatedAt),
        }
    )
    Internal.FieldsValue["f4f8"] = MakeDrawExt(Internal, HeaderValue)
    PropertyModel = MakeDrawRef(
        "moReferenceModel_c",
        NameValue,
        OwnerValue,
        ChildValue,
        EntryValue,
        BuildValue.TargetValue,
        None,
    )
    PropertyModel.FieldsValue.update({"f18": None, "f1f8": NameValue})
    Properties = ArchiveNode(RuntimeClass("suObArray", 1), {"items": ()})
    Manager.FieldsValue.update(
        {"n10": 1, "f08": ({"model": PropertyModel, "properties": Properties},)}
    )
    HeaderValue.FieldsValue["f30"] = ArchiveNode(
        RuntimeClass("moExtObjectList_c", 1), {"items": (EntryValue,)}
    )
    return DrawReferences(EntryValue, Internal, PropertyModel)
