from dataclasses import replace as ReplaceValue
from math import tau as FullTurn

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import KRefSupportSource, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Cold.ColdRevolve import (
    ColdRevolve,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Cold.IsColdRev import (
    IsColdRev,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.ReadRevGeom import (
    ReadRevGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import (
    ReadRevOwners,
)


# the actual support reference supersedes the provisional plane from keyword discovery
def ReadColdRev(
    Archive: SldprtArchive, Model: NativeModel, Settings: ReadOptions, BodyId: str
) -> tuple[NativeModel, ColdRevolve | None]:
    if Settings.extract_raw_brep or not IsColdRev(Archive, Model):
        return Model, None
    try:
        if Model.active_configuration_id != 0:
            raise ValueError("cache-free revolve requires configuration zero")
        LinkValue = ReadNativeLink(Archive, 0)
        (OwnerValue,) = ReadRevOwners(LinkValue)
        FrameValue = OwnerValue.FrameValue.SupportValue
        Reference = RequireNative(
            OwnerValue.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
        )
        PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
        if (
            type(PlaneId) is not int
            or FrameValue.z_axis.z != 0.0
            or OwnerValue.AngleValue.RadiansValue == FullTurn
        ):
            raise ValueError(
                "cache-free revolve requires a partial Top or Right support"
            )
        (SketchValue,) = Model.sketches
        Bound = ReplaceValue(
            Model,
            sketches=(
                ReplaceValue(
                    SketchValue,
                    support_plane_id=PlaneId,
                    support_plane=None,
                    support_source=KRefSupportSource,
                    unframed_support_plane_id=None,
                    TypedFrame=FrameValue,
                ),
            ),
        )
        Shape = ReadRevGeom(
            LinkValue,
            ReadCmgrMut(Archive.require("Contents/CMgr"), 19000),
            Bound,
            BodyId,
            OwnerValue,
        )
        return Bound, ColdRevolve(LinkValue, OwnerValue, Shape)
    except (ValueError, TypeError, KeyError, OverflowError) as ErrorInfo:
        if Settings.strict:
            raise SldprtFormat(
                "cache-free revolve has unverified typed history"
            ) from ErrorInfo
        return Model, None
