from collections.abc import Mapping
from math import cos, hypot, isclose, isfinite, sin
from xml.etree.ElementTree import Element as XmlElement

from convert.adapters.freecad.Native import TransformA
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropChild,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.geometry.Models.Transform import KOriginZero, Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# source placement words must describe a real rigid frame before the normal reader uses them
def ReadAxisWords(Properties: Mapping[str, object]) -> dict[str, float]:
    Record = ReadPropChild(Properties["Placement"], "Placement", "PropertyPlacement")
    Words = NativeRecord(Record["attributes"])
    RequireBox(
        set(Words) == {"Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3", "A", "Ox", "Oy", "Oz"}
        and not Record.get("children"),
        "FreeCAD origin axis has a different placement profile",
    )
    Numeric = {
        KeyValue: float(ReadBoxString(RawValue)) for KeyValue, RawValue in Words.items()
    }
    NormValue = hypot(*(Numeric[KeyValue] for KeyValue in ("Q0", "Q1", "Q2", "Q3")))
    RequireBox(
        all(isfinite(ValueNumber) for ValueNumber in Numeric.values())
        and isclose(NormValue, 1.0, rel_tol=0.0, abs_tol=1e-14),
        "FreeCAD origin axis has a nonrigid placement",
    )
    return Numeric


# both stored rotation forms must produce the same frame before the authoritative form is used
def ReadAxisFrame(Properties: Mapping[str, object]) -> Transform:
    Numeric = ReadAxisWords(Properties)
    Values = {KeyValue: str(Value) for KeyValue, Value in Numeric.items()}
    Quaternion = TransformA(XmlElement("PropertyPlacement", Values))
    AxisValue = tuple(Numeric[KeyValue] for KeyValue in ("Ox", "Oy", "Oz"))
    NormValue = hypot(*AxisValue)
    RequireBox(
        0.0 < NormValue and isfinite(NormValue),
        "FreeCAD origin has a malformed rotation axis",
    )
    HalfAngle = Numeric["A"] / 2.0
    Factor = sin(HalfAngle)
    Rotation = tuple((Component / NormValue) * Factor for Component in AxisValue)
    Values.update(zip(("Q0", "Q1", "Q2", "Q3"), map(str, (*Rotation, cos(HalfAngle)))))
    Restored = TransformA(XmlElement("PropertyPlacement", Values))
    RequireBox(
        all(
            isclose(LeftValue, RightValue, rel_tol=0.0, abs_tol=1e-14)
            for First, Other in zip(
                (Restored.x_axis, Restored.y_axis, Restored.z_axis),
                (Quaternion.x_axis, Quaternion.y_axis, Quaternion.z_axis),
                strict=True,
            )
            for LeftValue, RightValue in zip(
                (First.x, First.y, First.z), (Other.x, Other.y, Other.z), strict=True
            )
        ),
        "FreeCAD origin axis angle disagrees with its stored quaternion",
    )
    return Restored


# the source line projects its own local x basis onto the required principal direction
def ReadAxisPlace(
    Properties: Mapping[str, object], DirectionValue: SpaceVector
) -> Transform:
    FrameValue = ReadAxisFrame(Properties)
    Actual = FrameValue.x_axis
    RequireBox(
        FrameValue.origin == KOriginZero
        and all(
            isclose(FirstValue, OtherValue, rel_tol=0.0, abs_tol=1e-14)
            for FirstValue, OtherValue in zip(
                (Actual.x, Actual.y, Actual.z),
                (DirectionValue.x, DirectionValue.y, DirectionValue.z),
                strict=True,
            )
        ),
        "FreeCAD origin axis does not match its owned principal direction",
    )
    return FrameValue
