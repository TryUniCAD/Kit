from math import tau as FullTurn

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Cold.BindColdSketch import (
    BindColdSketch,
)
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
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.IsThinRev import (
    IsThinRev,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadColdThin import (
    ReadColdThin,
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
        if IsThinRev(Model):
            return ReadColdThin(
                LinkValue,
                ReadCmgrMut(Archive.require("Contents/CMgr"), 19000),
                Model,
                BodyId,
            )
        (OwnerValue,) = ReadRevOwners(LinkValue)
        if (
            OwnerValue.FrameValue.SupportValue.z_axis.z != 0.0
            or OwnerValue.AngleValue.RadiansValue == FullTurn
        ):
            raise ValueError(
                "cache-free revolve requires a partial Top or Right support"
            )
        Bound = BindColdSketch(Model, OwnerValue)
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
