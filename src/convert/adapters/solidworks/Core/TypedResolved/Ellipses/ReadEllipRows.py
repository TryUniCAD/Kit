from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import (
    EntityFields,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.SketchArrays import (
    KSketchArrays,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

# the compact indices identify five geometry roles and the shared endpoint separately
KEllipOrdinals = ("fdc_s", "fc8_s", "fe0_s", "fe4_s", "fe8_s", "fec_s")


# the solver and miscellaneous sketch arrays must carry no unprojected authored state
def CheckEllipSk(SketchValue: ArchiveNode) -> None:
    Fields = SketchValue.FieldsValue
    for CountName, FieldName in KSketchArrays:
        if FieldName not in ("points", "ellipses") and (
            Fields.get(CountName) != 0 or not IsLineState(Fields.get(FieldName))
        ):
            raise ValueError("ellipse sketch has other modeling entities or helpers")
    if (
        Fields.get("npoints") != 6
        or Fields.get("nellipses") != 1
        or any(
            not IsLineState(Fields.get(NameValue))
            for NameValue in ("dims", "coinc", "f590", "f5d8", "f580", "f598", "f588")
        )
        or Fields.get("f570") != dict.fromkeys("xyz", 0.0)
        or any(
            Fields.get(NameValue) != 0
            for NameValue in ("f37c", "f188", "f18c", "f190", "f578", "f134")
        )
        or Fields.get("f128") != 1
        or Fields.get("f12c") != 1
        or Fields.get("f130") != 2
        or Fields.get("f56c") != 2
    ):
        raise ValueError(
            "ellipse sketch has retained constraints or alternate creation state"
        )


# the sole free ellipse has one distinct two use seam and five actual point owners
def ReadEllipRows(
    SketchValue: ArchiveNode,
) -> tuple[int, tuple[Mapping[str, object], ...]]:
    CheckEllipSk(SketchValue)
    Fields = SketchValue.FieldsValue
    Defaults = EntityFields(SketchValue)
    (ItemValue,) = NativeRows(Fields.get("ellipses"))
    Ellipse = NativeRecord(ItemValue.get("ellipse"))
    Ordinals = tuple(Ellipse.get(NameValue) for NameValue in KEllipOrdinals)
    SegmentId = Ellipse.get("f0c")
    if (
        ItemValue.get("flags") != 0
        or any(type(Ordinal) is not int for Ordinal in Ordinals)
        or set(Ordinals) != set(range(6))
        or Ellipse.get("fcc_s") != Ordinals[1]
        or type(SegmentId) is not int
        or SegmentId != 1
        or Ellipse.get("f08") != 1
        or any(
            Ellipse.get(NameValue) != DefaultValue
            for NameValue, DefaultValue in Defaults.items()
            if NameValue not in ("_sketch", "f08", "f0c")
        )
        or any(
            Ellipse.get(NameValue) != Expected
            for NameValue, Expected in (
                ("fd0", 1),
                ("fd4", 0),
                ("fd8", 1),
                ("seg_tol", -1.0),
            )
        )
    ):
        raise ValueError(
            "ordinary full ellipse has different endpoints or authored entity modes"
        )
    PointRows = NativeRows(Fields.get("points"))
    if len(PointRows) != 6 or any(RowValue.get("kind") != 0 for RowValue in PointRows):
        raise ValueError("ordinary full ellipse has unsupported point encoding")
    Points = tuple(
        NativeRecord(PointRows[Ordinal].get("point"))
        for Ordinal in Ordinals
        if type(Ordinal) is int
    )
    CheckEllipPoint(Points, Defaults)
    return SegmentId, Points


# the free geometry branch admits only ordinary undecorated point owners without extra spatial intent
def CheckEllipPoint(
    Points: tuple[Mapping[str, object], ...],
    Defaults: Mapping[str, object],
) -> None:
    for PointValue in Points:
        if (
            any(
                PointValue.get(NameValue) != Defaults[NameValue]
                for NameValue in Defaults
                if NameValue not in ("_sketch", "f08", "f0c")
            )
            or PointValue.get("pflags") != 0x1E
            or PointValue.get("f108") != -2
            or PointValue.get("has_jet") != 0
            or any(
                PointValue.get(NameValue) != {"x": 0.0, "y": 0.0}
                for NameValue in ("p1", "p2")
            )
        ):
            raise ValueError("ellipse has unsupported point style or solver state")


# mapped handles are local to the unique ellipse row and must not appear on axis points
def ReadEllipHandle(
    Points: tuple[Mapping[str, object], ...],
) -> tuple[ArchiveNode, tuple[int, ...]]:
    Handle = RequireNative(Points[1].get("h1"), "sgEllipseHandle")
    Result: list[int] = []
    if Handle.ClassValue != RuntimeClass(
        "sgEllipseHandle", 1
    ) or Handle.FieldsValue != {"idx": 0, "f1c": -1, "f08": 0}:
        raise ValueError("ellipse seam handle does not select its actual owned row")
    for Index, PointValue in enumerate(Points):
        Identity = PointValue.get("f0c")
        IsSeam = Index == 1
        if (
            type(Identity) is not int
            or PointValue.get("f08") != 0
            or PointValue.get("h1") is not (Handle if IsSeam else None)
            or PointValue.get("h2") is not None
            or PointValue.get("fe4") != (2 if IsSeam else 0 if Index == 0 else 3)
            or PointValue.get("fe8") != (2 if IsSeam else 1)
            or PointValue.get("fec") != int(Index == 0)
            or PointValue.get("ff0") != 0
        ):
            raise ValueError(
                "ellipse seam and four axis points must retain separate live owner roles"
            )
        Result.append(Identity)
    if set(Result) != set(range(1, 7)):
        raise ValueError(
            "ellipse point identities collide or leave the actual created contour"
        )
    return Handle, tuple(Result)
