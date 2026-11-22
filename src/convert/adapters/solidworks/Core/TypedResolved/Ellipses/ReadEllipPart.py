from dataclasses import replace as ReplaceValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.CheckEllipArch import (
    CheckEllipArch,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    EllipPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.ProjectEllip import (
    ProjectEllip,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.ReadEllipRows import (
    ReadEllipHandle,
    ReadEllipRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import KTransformIdentity


# the actual sketch datum and live blind parameter must join the published feature identities
def ReadEllipPart(Archive: SldprtArchive, ModelValue: NativeModel) -> EllipPartRead:
    LinkValue = ReadNativeLink(
        Archive, ModelValue.active_configuration_id, ReadEllipses=True
    )
    Features = IndexFeatures(LinkValue)
    (Sketch,) = ModelValue.sketches
    (Operation,) = ModelValue.operations
    BossValue = ReadExtrude(LinkValue, Features[Operation.object_id], Features)
    ProfileValue = BossValue.ProfileValue
    RootValue = LinkValue.ConfigValue.RootValue
    Reference = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    Driver = BossValue.DepthValue.DepthValue
    if (
        BossValue.ParentsValue != (ProfileValue,)
        or BossValue.NodeValue is not LinkValue.ResolvedValue.RootsValue[-1]
        or ReadPrismFrame(ProfileValue, RootValue, Features) != KTransformIdentity
        or NativeNodeId(ProfileValue) != Sketch.object_id
        or Operation.profile_id != Sketch.object_id
        or NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
        != Sketch.support_plane_id
        or Driver.name != "D1"
        or set(Features) != {Value.object_id for Value in ModelValue.features}
    ):
        raise ValueError(
            "SOLIDWORKS ellipse lacks its linked Front profile and live D1"
        )
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    SegmentId, PointsValue = ReadEllipRows(SketchValue)
    Handle, PointIds = ReadEllipHandle(PointsValue)
    Geometry = ProjectEllip(PointsValue, RequireScalar(Driver.native_value))
    PlanValue = CheckEllipArch(Archive, LinkValue, BossValue, PointsValue)
    return EllipPartRead(
        LinkValue,
        BossValue,
        SketchValue,
        Handle,
        Geometry,
        SegmentId,
        PointIds,
        PlanValue,
    )


# an actual typed descriptor in any active sketch requires explicit conic admission
def HasEllipSketch(ModelValue: NativeModel) -> bool:
    return any(
        Value.name == "sgEllipseHandle"
        and any(
            SketchValue.native_offset <= Value.offset < SketchValue.native_end
            for SketchValue in ModelValue.sketches
        )
        for Value in ModelValue.classes
    )


# the verified read boundary requires the only modeled cold profile and its one final boss
def ReadScopeEllip(Archive: SldprtArchive, ModelValue: NativeModel) -> EllipPartRead:
    if (
        Archive.format_version != 4
        or len(ModelValue.sketches) != 1
        or tuple(Value.kind for Value in ModelValue.operations) != ("join",)
        or KPartitionStream in Archive.streams
        or len(Archive.records) != 10
        or ModelValue.equations
        or tuple(
            (Value.configuration_id, Value.name) for Value in ModelValue.configurations
        )
        != ((0, "Default"),)
    ):
        raise SldprtFormat(
            "SOLIDWORKS full ellipse is outside the verified cold archive profile"
        )
    try:
        return ReadEllipPart(Archive, ModelValue)
    except (ValueError, TypeError, KeyError, OverflowError) as ErrorInfo:
        raise SldprtFormat(
            "SOLIDWORKS full ellipse lacks its verified cold owners"
        ) from ErrorInfo


# strict reads refuse unsupported ellipse history while permissive inspection retains a diagnostic
def TryEllipPart(
    Archive: SldprtArchive, ModelValue: NativeModel, Settings: ReadOptions
) -> tuple[NativeModel, EllipPartRead | None]:
    if Settings.extract_raw_brep or not HasEllipSketch(ModelValue):
        return ModelValue, None
    try:
        return ModelValue, ReadScopeEllip(Archive, ModelValue)
    except SldprtFormat as ErrorInfo:
        if Settings.strict:
            raise
        return (
            ReplaceValue(
                ModelValue,
                diagnostics=(*ModelValue.diagnostics, str(ErrorInfo)),
            ),
            None,
        )
