from collections.abc import Mapping
from math import hypot as Hypot, isfinite as IsFinite, ulp as FloatStep
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckCacheFace import (
    CheckCacheFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# chooser cache arrays cannot substitute a foreign object for the actual creating boss
def ReadCacheRows(
    BossValue: ArchiveNode, NameValue: str, Expected: int
) -> tuple[Mapping[str, object], ...]:
    Chooser = NativeRecord(BossValue.FieldsValue.get(NameValue))
    ListValue = NativeRecord(Chooser.get("f48"))
    RowsValue = NativeRows(ListValue.get("items"))
    if (
        Chooser.get("f68") is not BossValue
        or ListValue.get("n") != len(RowsValue)
        or len(RowsValue) != Expected
    ):
        raise ValueError(
            "SOLIDWORKS attached circle chooser does not alias its own producer"
        )
    return RowsValue


# cap history may store the retired blind length but cannot introduce active selections or operators
def ReadChooser(
    RowValue: Mapping[str, object], BossValue: ArchiveNode, ArcMark: int
) -> tuple[tuple[tuple[ArchiveNode, ArchiveNode, ArchiveNode], ...], ArchiveNode]:
    ItemValue = RequireNative(RowValue.get("o"), "moPerBodyChooserData_c").FieldsValue
    Faces = NativeRecord(ItemValue.get("f08"))
    Bounds = NativeRecord(ItemValue.get("f48"))
    Flags = NativeRecord(ItemValue.get("f78"))
    if (
        not IsLineState(ItemValue.get("f28"))
        or any(ItemValue.get(NameValue) != 0 for NameValue in ("f68", "f6c", "f70"))
        or (Faces.get("n"), Bounds.get("n"), Flags.get("n")) != (2, 1, 1)
        or NativeRows(Flags.get("items")) != ({"v": 0},)
    ):
        raise ValueError(
            "SOLIDWORKS attached circle chooser carries additional selection state"
        )
    FacesValue = tuple(
        CheckCacheFace(
            RequireNative(RowValue.get("o"), "moFaceRef_c"),
            BossValue,
            CapValue,
            ArcMark,
        )
        for CapValue, RowValue in zip(
            range(2), NativeRows(Faces.get("items")), strict=True
        )
    )
    (BoundsRow,) = NativeRows(Bounds.get("items"))
    return FacesValue, RequireNative(BoundsRow.get("o"), "moBBoxCenterData_c")


# the stored chooser bounds describe the retained inactive cylinder rather than the edited live depth
def CheckCacheBox(Bounds: ArchiveNode, CircleValue: LocalCircle, Depth: float) -> None:
    Fields = Bounds.FieldsValue
    Center = NativeRecord(Fields.get("f10"))
    Diameter = 2 * CircleValue.RadiusValue / 1000
    Expected = (*CircleValue.CenterMetres, Depth / 2, Hypot(Diameter, Diameter, Depth))
    if Fields.get("f08") != 1:
        raise ValueError("SOLIDWORKS attached circle has alternate chooser bounds")
    for Value, Target in zip(
        (Center.get("x"), Center.get("y"), Center.get("z"), Fields.get("f28")),
        Expected,
        strict=True,
    ):
        if (
            type(Value) is not float
            or not IsFinite(Value)
            or abs(Value - Target) > 4 * FloatStep(Target)
        ):
            raise ValueError(
                "SOLIDWORKS attached circle chooser bounds disagree with its inactive depth"
            )


# the file identity is a stored self reference and never needs to be loaded to resolve the local body
def CheckCacheFile(
    LinkValue: NativeLink, FileValue: ArchiveNode, Configuration: str
) -> None:
    RootFields = LinkValue.ConfigValue.RootValue.FieldsValue
    ModelName = RequireNative(RootFields.get("f18"), "moNodeName_c").FieldsValue.get(
        "f08"
    )
    Fields = FileValue.FieldsValue
    Shared = NativeRecord(Fields.get("shared"))
    PartText = RequireNative(Shared.get("h10"), "moCStringHandle_c").FieldsValue.get(
        "f08"
    )
    PathValue = RequireNative(Shared.get("h18"), "moCStringHandle_c").FieldsValue.get(
        "f08"
    )
    Config = NativeRecord(Fields.get("refcfg"))
    if (
        type(ModelName) is not str
        or type(PathValue) is not str
        or PartText != ModelName
        or PureWindowsPath(PathValue).name.casefold()
        != (ModelName + KPartSuffix).casefold()
        or Shared.get("f28") != LinkValue.ConfigValue.HeaderValue.FieldsValue.get("f70")
        or (Config.get("f08"), Config.get("f10")) != (Configuration, 0)
    ):
        raise ValueError(
            "SOLIDWORKS attached circle chooser file does not identify its own part"
        )


# live radial edits remain portable when chooser records only snapshot the same prior local body
def CheckBodyCache(
    LinkValue: NativeLink,
    BossValue: ArchiveNode,
    CircleValue: LocalCircle,
    InactiveDepth: float,
    Configuration: str,
) -> None:
    (First,) = ReadCacheRows(BossValue, "f4a8", 1)
    _ = ReadCacheRows(BossValue, "f4b0", 0)
    (LastRow,) = ReadCacheRows(BossValue, "f4c0", 1)
    FirstRefs, FirstBox = ReadChooser(First, BossValue, CircleValue.ArcMark)
    LastRefs, LastBox = ReadChooser(LastRow, BossValue, CircleValue.ArcMark)
    if FirstRefs != LastRefs or FirstRefs[0][-1] is not FirstRefs[1][-1]:
        raise ValueError(
            "SOLIDWORKS attached circle chooser has conflicting historical face identities"
        )
    CheckCacheFile(LinkValue, FirstRefs[0][-1], Configuration)
    CheckCacheBox(FirstBox, CircleValue, InactiveDepth)
    CheckCacheBox(LastBox, CircleValue, InactiveDepth)
