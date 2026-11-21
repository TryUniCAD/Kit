from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxRelease import (
    ReadBoxExts,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KFeatureProps,
    KNewFeatProps,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# the document object table names every actual owner in the measured primitive
def ReadBoxObjects(
    Source: Mapping[str, object],
    FeatureData: Mapping[str, object],
    BodyData: Mapping[str, object],
    Release: str,
) -> dict[str, Mapping[str, object]]:
    PartName = ReadBoxString(FeatureData["name"])
    BodyName = ReadBoxString(BodyData["name"])
    Objects = NativeRows(Source["objects"])
    Known = {ReadBoxString(RowValue["name"]): RowValue for RowValue in Objects}
    Expected = {
        BodyName: "PartDesign::Body",
        PartName: "PartDesign::AdditiveBox",
        "Origin": "App::Origin",
        **{AxisName + "_Axis": "App::Line" for AxisName in ("X", "Y", "Z")},
        **{PlaneName + "_Plane": "App::Plane" for PlaneName in ("XY", "XZ", "YZ")},
    }
    if Release == "1.1":
        Expected["Origin001"] = "App::Point"
    RequireBox(
        {NameValue: RowValue["type_id"] for NameValue, RowValue in Known.items()}
        == Expected
        and len(Objects) == len(Expected),
        "FreeCAD source includes another modeled object",
    )
    RequireBox(
        Known[PartName] == FeatureData and Known[BodyName] == BodyData,
        "FreeCAD primitive or Body differs from its source object owner",
    )
    return Known


# the release property roster and actual support determine the admitted dependencies
def ReadBoxProps(
    FeatureData: Mapping[str, object],
    BodyName: str,
    Release: str,
    *,
    TopAttached: bool = True,
) -> Mapping[str, object]:
    Properties = NativeRecord(FeatureData["properties"])
    Expected = KFeatureProps
    if Release != "0.21":
        Expected = (Expected - {"Support"}) | KNewFeatProps
    if Release == "1.1":
        Expected |= {"FuzzyTolerance"}
    RequireBox(
        frozenset(Properties) == Expected
        and FeatureData["type_id"] == "PartDesign::AdditiveBox"
        and not FeatureData["touched"],
        "FreeCAD primitive property layout differs from the documented profile",
    )
    RequireBox(
        FeatureData["extensions"] == ReadBoxExts(Release)
        and FeatureData["dependencies"]
        == ([BodyName, "XZ_Plane"] if TopAttached else [BodyName]),
        "FreeCAD primitive uses another attachment engine or owner",
    )
    return Properties
