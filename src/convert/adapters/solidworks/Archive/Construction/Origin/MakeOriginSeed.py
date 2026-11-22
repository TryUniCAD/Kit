from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import (
    MakeProfileData,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# origin profiles apply their own native reference mode transition after constructing the shared complete profile state
def MakeOriginSeed(
    SketchValue: ArchiveNode, Reference: ArchiveNode, FrameValue: PlaneFrame
) -> dict[str, object]:
    FieldsValue = MakeProfileData(SketchValue, Reference, FrameValue)
    FieldsValue["pd_f11c"] = -1 & ~6
    return FieldsValue
