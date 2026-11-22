from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipsePart import (
    BuildEllipPart,
)
from convert.adapters.solidworks.Archive.Construction.Model.GraphValue import FieldInt
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.ProjectEllip import (
    ReadEllipXY,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# all streams must agree with the canonical cold model before exposing its derived geometry
def CheckEllipArch(
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    OwnerValue: ExtrudeOwner,
    PointsValue: tuple[Mapping[str, object], ...],
) -> None:
    HeaderFields = LinkValue.ConfigValue.HeaderValue.FieldsValue
    TimeValue = FieldInt(HeaderFields, "f70")
    SelfValue = GetFileRef(HeaderFields.get("f38"))
    if TimeValue <= 0:
        raise ValueError("SOLIDWORKS cold ellipse requires a positive creation event")
    PlanValue = EllipsePlan(
        ReadNativeName(LinkValue.ConfigValue.RootValue),
        "Default",
        "Front Plane",
        ReadNativeName(OwnerValue.ProfileValue),
        ReadNativeName(OwnerValue.NodeValue),
        RequireScalar(OwnerValue.DepthValue.DepthValue.native_value),
        ReadEllipXY(PointsValue[0]),
        ReadEllipXY(PointsValue[2]),
        ReadEllipXY(PointsValue[3]),
    )
    Recipe = MakePartRecipe(PlanValue, TimeValue)
    OutputValue = RequirePartPath(SelfValue.PathValue, TimeValue)
    Expected = BuildEllipPart(PlanValue, ReplaceValue(Recipe, OutputValue=OutputValue))
    Names = tuple(Record.name for Record in Archive.records)
    if (
        Names != tuple(Expected.StreamsValue)
        or Archive.streams != Expected.StreamsValue
    ):
        raise ValueError("SOLIDWORKS cold ellipse contains unprojected archive state")
