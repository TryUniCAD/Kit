from collections.abc import Mapping
from math import isclose, pi, sqrt

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckIdentity import (
    CheckIdentity,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxMat import (
    ReadBoxMat,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadEnumText import (
    ReadEnumText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropChild,
    ReadPropText,
    RequireEmpty,
    RequireProp,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# the source support must be the whole xz datum with its authored positive quarter turn
def CheckTopPlace(Properties: Mapping[str, object], Release: str) -> None:
    CheckIdentity(Properties, "AttachmentOffset")
    Placement = ReadPropChild(Properties["Placement"], "Placement", "PropertyPlacement")
    Attributes = NativeRecord(Placement["attributes"])
    Position = tuple(
        float(ReadBoxString(Attributes[FieldName]))
        for FieldName in ("Px", "Py", "Pz", "Ox", "Oy", "Oz")
    )
    Rotation = tuple(
        float(ReadBoxString(Attributes[FieldName]))
        for FieldName in ("Q0", "Q1", "Q2", "Q3", "A")
    )
    HalfAngle = sqrt(0.5)
    RequireBox(
        Position == (0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        and all(
            isclose(Actual, Target, abs_tol=1e-14, rel_tol=0.0)
            for Actual, Target in zip(
                Rotation, (HalfAngle, 0.0, 0.0, HalfAngle, pi / 2), strict=True
            )
        ),
        "FreeCAD attached box does not resolve to a positive quarter-turn about model X",
    )
    Support = "Support" if Release == "0.21" else "AttachmentSupport"
    Links = ReadPropChild(Properties[Support], "LinkSubList", "LinkSubList")
    RequireBox(
        Links["attributes"] == {"count": "1"}
        and Links["children"]
        == [
            {"tag": "Link", "attributes": {"obj": "XZ_Plane", "sub": ""}},
        ],
        "FreeCAD attached box must select exactly its actual whole XZ plane",
    )


# release dependent attachment and material owners remain literal properties of the primitive
def ReadAttachText(Properties: Mapping[str, object], Release: str) -> dict[str, str]:
    if Release == "0.21":
        return {}
    RequireBox(
        ReadEnumText(Properties, "AttacherEngine") == "Engine 3D",
        "FreeCAD box has an unqualified named attachment engine",
    )
    RequireProp(Properties, "Suppressed", "Bool", "Bool", "false")
    Cache = NativeRecord(Properties["SuppressedShape"])
    RequireBox(
        Cache["tag"] == "Property"
        and NativeRecord(Cache["attributes"])["type"] == "Part::PropertyPartShape",
        "FreeCAD suppression cache has an unqualified property type",
    )
    Output = {
        "FreeCAD Feature Material UUID": ReadBoxMat(Properties),
        "FreeCAD Feature Refine": ReadPropText(Properties, "Refine", "Bool", "Bool"),
    }
    if Release == "1.1":
        Tolerance = ReadPropText(
            Properties, "FuzzyTolerance", "FloatConstraint", "Float"
        )
        RequireBox(
            float(Tolerance) == -1.0, "FreeCAD box has an active fuzzy tolerance"
        )
        Output["FreeCAD Feature Fuzzy Tolerance"] = Tolerance
    return Output


# only the documented support mode without extra modeled inputs reaches lowering
def CheckBoxAttach(
    Properties: Mapping[str, object], FeatureName: str, PlaneId: str, Release: str
) -> dict[str, str]:
    CheckTopPlace(Properties, Release)
    RequireProp(Properties, "BaseFeature", "Link", "Link", "")
    RequireProp(
        Properties, "AttacherType", "String", "String", "Attacher::AttachEngine3D"
    )
    MapMode = ReadPropText(Properties, "MapMode", "Enumeration", "Integer")
    RequireBox(
        MapMode == "5", "FreeCAD property MapMode is outside the admitted box policy"
    )
    RequireProp(Properties, "MapReversed", "Bool", "Bool", "false")
    Refine = ReadPropText(Properties, "Refine", "Bool", "Bool")
    RequireBox(
        Refine in (("false",) if Release == "0.21" else ("false", "true")),
        "FreeCAD box has an unqualified refinement state",
    )
    RequireProp(Properties, "Visibility", "Bool", "Bool", "true")
    RequireProp(Properties, "Label", "String", "String", FeatureName)
    RequireProp(Properties, "Label2", "String", "String", "")
    RequireEmpty(Properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    RequireBox(
        float(ReadPropText(Properties, "MapPathParameter", "Float", "Float")) == 0.0,
        "FreeCAD attachment has an active path coordinate",
    )
    return ReadAttachText(Properties, Release) | {
        "FreeCAD Attachment Support Id": PlaneId,
        "FreeCAD Attachment Map Mode": MapMode,
    }
