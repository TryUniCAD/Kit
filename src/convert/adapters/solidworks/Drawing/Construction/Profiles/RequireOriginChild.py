from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)


# origin display selection must use the actual generated child feature before any drawing owner can be changed
def NeedOriginChild(ChildValue: PartCandidate) -> ArchiveNode:
    if type(CastValue(object, ChildValue)) is not PartCandidate:
        raise TypeError("origin display requires the actual generated SDK child")
    OriginValue = ChildValue.SystemValue.OriginValue
    ProfileValue = NeedProfileNode(OriginValue.ProfileValue, "moOriginProfileFeature_c")
    OwnerValue = NeedProfileNode(ChildValue.SystemValue.RootValue, "moPart_c")
    FieldsValue = ProfileValue.FieldsValue
    if (
        FieldsValue.get("owner") is not OwnerValue
        or FieldsValue.get("pd_f80") is not OriginValue.SketchValue
        or FieldsValue.get("pd_f110") is not None
        or FieldsValue.get("f3dc") != 0
        or ReadBlankKids(ProfileValue)
        or not 0 <= FieldInt(FieldsValue, "f08") < 0x7FFFFFFF
    ):
        raise ValueError(
            "origin display requires the actual registered fresh child origin"
        )
    return ProfileValue
