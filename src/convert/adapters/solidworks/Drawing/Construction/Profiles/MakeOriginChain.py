from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeRefChain import (
    MakeRefChain,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)


# each display owns its component wrapper while its reference path must retain the real view internal reference
def MakeOriginChain(OwnerValue: ArchiveNode, Reference: ArchiveNode) -> ArchiveNode:
    _ = NeedProfileNode(OwnerValue, "moDrawing_c")
    _ = NeedProfileNode(Reference, "moReferenceInternal_c")
    External = NeedProfileNode(Reference.FieldsValue.get("f4f8"), "moExtFeature_c")
    if (
        Reference.FieldsValue.get("owner") is not OwnerValue
        or External.FieldsValue.get("f50") is not Reference
        or FieldInt(External.FieldsValue, "f44")
        != FieldInt(Reference.FieldsValue, "f08")
    ):
        raise ValueError(
            "origin display requires its actual drawing external reference"
        )
    return ArchiveNode(
        RuntimeClass("moChainComponent_c", 1),
        {
            "owner": OwnerValue,
            "f20": MakeRefChain(External),
            "f30": (101 + FieldInt(Reference.FieldsValue, "f3f0")) & 0xFFFFFFFF,
        },
    )
