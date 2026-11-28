from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.BuildCircGeom import (
    BuildCircGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.BindColdOff import (
    BindColdOff,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# a recognized offset part must reject contradictory ownership before the generic reader can infer placement
def TryColdOff(
    Archive: SldprtArchive,
    ModelValue: NativeModel,
    SettingsValue: ReadOptions,
    BodyId: str,
) -> tuple[NativeModel, PartGeometry | None] | None:
    if not IsCacheAbsent(Archive) or all(
        Plane.principal for Plane in ModelValue.planes
    ):
        return None
    try:
        LinkValue = ReadNativeLink(Archive, ModelValue.active_configuration_id)
        Features = IndexFeatures(LinkValue)
    except (KeyError, TypeError, ValueError):
        return None
    Offsets = tuple(
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moRefPlane_c"
        and isinstance((DataValue := NodeValue.FieldsValue.get("f6f8")), ArchiveNode)
        and DataValue.ClassValue.NameValue == "moFaceRefPlnData_c"
    )
    if not Offsets:
        return None
    try:
        (DatumValue,) = Offsets
        ManagerValue = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        ModelValue, PlanValue = BindColdOff(
            ModelValue, LinkValue, ManagerValue, Features, DatumValue
        )
        return ModelValue, (
            BuildCircGeom(PlanValue, BodyId) if SettingsValue.include_brep else None
        )
    except (KeyError, TypeError, ValueError, OverflowError) as ErrorInfo:
        if SettingsValue.strict:
            raise SldprtFormat(
                f"unsupported typed offset-plane part: {ErrorInfo}"
            ) from ErrorInfo
        return None
