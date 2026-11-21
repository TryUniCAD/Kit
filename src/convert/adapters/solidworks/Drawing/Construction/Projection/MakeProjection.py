from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.MakeViewBox import (
    MakeViewBox,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.MakeViewFrame import (
    MakeViewFrame,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.ReadChildView import (
    ReadChildView,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.ReadViewBox import (
    ReadViewBox,
)
from convert.adapters.solidworks.Drawing.Construction.Projection.ViewProjection import (
    ViewProjection,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinViewOwners import (
    KViewDirections,
)
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.geometry.Models.VectorPlane import PlaneVector


# canonical model rotation and the actual prism determine centred placement outlines and distinct sheet and model support frames
def MakeProjection(
    ChildValue: PartCandidate, SheetValue: DrawingSheet, ViewValue: DrawingView
) -> ViewProjection:
    if (
        type(SheetValue) is not DrawingSheet
        or type(ViewValue) is not DrawingView
        or not isinstance(ViewValue.OrientationName, str)
        or ViewValue.OrientationName not in KViewDirections
        or type(ViewValue.ScaleRatio) is not tuple
        or type(ViewValue.PositionValue) is not PlaneVector
    ):
        raise ValueError(
            "drawing projection requires explicit ordinary sheet and view intent"
        )
    Numerator, Denominator = (NeedDrawNumber(Value) for Value in ViewValue.ScaleRatio)
    ScaleValue = Numerator / Denominator if Denominator > 0 else 0.0
    if (
        Numerator <= 0
        or Denominator != 1.0
        or ScaleValue <= 0
        or not IsFinite(ScaleValue)
        or not IsFinite(1.0 / ScaleValue)
    ):
        raise ValueError(
            "drawing projection requires the qualified explicit scalar view scale"
        )
    ModelBox = ReadViewBox(ChildValue)
    Centre = tuple(ModelBox[f"b{Index}"] for Index in range(3))
    Origin = (
        NeedDrawNumber(ViewValue.PositionValue.XCoord),
        NeedDrawNumber(ViewValue.PositionValue.YCoord),
        0.0,
    )
    Rotation, AxesValue = ReadChildView(ChildValue, ViewValue.OrientationName)
    RotatedCentre = tuple(
        sum(Value * AxisValue for Value, AxisValue in zip(Centre, Basis, strict=True))
        for Basis in AxesValue
    )
    GeometricScale = 1.0 if abs(ScaleValue - 1.0) <= 1e-8 else ScaleValue
    Translation = tuple(
        LeftValue - GeometricScale * RightValue
        for LeftValue, RightValue in zip(Origin, RotatedCentre, strict=True)
    )
    HalfLengths = tuple(ModelBox[f"b{Index + 3}"] - Centre[Index] for Index in range(3))
    HalfWidth, HalfHeight = (
        GeometricScale
        * sum(
            Length * abs(AxisValue)
            for Length, AxisValue in zip(HalfLengths, Basis, strict=True)
        )
        for Basis in AxesValue[:2]
    )
    XValue, YValue = Origin[:2]
    Projected = (
        XValue - HalfWidth,
        YValue - HalfHeight,
        XValue + HalfWidth,
        YValue + HalfHeight,
    )
    Margin = (
        min(
            NeedDrawNumber(SheetValue.SheetWidth),
            NeedDrawNumber(SheetValue.SheetHeight),
        )
        * 0.02
    )
    Outline = tuple(
        Value + Delta
        for Value, Delta in zip(
            Projected, (-Margin, -Margin, Margin, Margin), strict=True
        )
    )
    HeaderBounds = MakeViewBox(
        (Outline[0], Outline[1], 0.0), (Outline[2], Outline[3], 0.0)
    )
    HeaderBounds.update(zip(("b0", "b1", "b2"), Origin, strict=True))
    FieldsValue: dict[str, object] = {
        "f5e0": MakeViewFrame(Translation, ScaleValue, Rotation),
        "f778": dict(zip("xyz", Origin, strict=True)),
        "f600": ModelBox,
        "has_f648": 1,
        "f648": dict(zip("xyz", Centre, strict=True)),
        "f780": Numerator,
        "f788": Denominator,
        "f1010": KViewDirections[ViewValue.OrientationName],
        "f1018": ViewValue.OrientationName,
    }
    FieldsValue.update(zip(("f6d8", "f6e0", "f6e8", "f6f0"), Outline, strict=True))
    FieldsValue.update(
        zip(
            ("f718", "f720", "f728", "f730", "f738", "f740", "f748", "f750"),
            (*Projected, *Projected),
            strict=True,
        )
    )
    return ViewProjection(
        FieldsValue,
        HeaderBounds,
        MakeViewFrame(tuple(-Value / ScaleValue for Value in Origin), 1.0 / ScaleValue),
        MakeViewFrame(tuple(-Value for Value in RotatedCentre), 1.0, Rotation),
        AxesValue,
    )
