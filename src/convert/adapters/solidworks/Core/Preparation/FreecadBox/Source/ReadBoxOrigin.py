from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckIdentity import (
    CheckIdentity,
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
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# the declared origin group must own every datum used by the attached feature
def CheckOrigLinks(
    Origin: Mapping[str, object], Properties: Mapping[str, object], Release: str
) -> None:
    Owners = ("X_Axis", "Y_Axis", "Z_Axis", "XY_Plane", "XZ_Plane", "YZ_Plane")
    Expected = (*Owners, "Origin001") if Release == "1.1" else Owners
    Children = ReadPropChild(Properties["OriginFeatures"], "LinkList", "LinkList")
    Records = NativeRows(Children["children"])
    Actual = tuple(
        NativeRecord(RowValue["attributes"])["value"] for RowValue in Records
    )
    RequireBox(
        NativeRecord(Children["attributes"])["count"] == str(len(Expected))
        and Actual == Expected
        and all(RowValue["tag"] == "Link" for RowValue in Records)
        and Origin["dependencies"] == list(Expected)
        and not Origin["touched"],
        "FreeCAD origin has another owned source datum",
    )


# the newer source origin also carries its own independently validated authored point
def ReadBoxOrigin(
    Objects: Mapping[str, Mapping[str, object]],
    Release: str,
) -> dict[str, str]:
    Origin = Objects["Origin"]
    Properties = NativeRecord(Origin["properties"])
    CheckOrigLinks(Origin, Properties, Release)
    if Release != "1.1":
        return {}
    CheckIdentity(Properties, "Placement")
    RecordValue = Objects["Origin001"]
    PointProps = NativeRecord(RecordValue["properties"])
    RequireBox(
        set(PointProps)
        == {"ExpressionEngine", "Label", "Label2", "Placement", "Role", "Visibility"}
        and not (
            RecordValue["touched"]
            or RecordValue["dependencies"]
            or RecordValue["extensions"]
        ),
        "FreeCAD origin point has an unqualified property or owner",
    )
    CheckIdentity(PointProps, "Placement")
    RequireEmpty(PointProps, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    RequireProp(PointProps, "Role", "String", "String", "Origin")
    RequireProp(PointProps, "Label2", "String", "String", "")
    RequireProp(PointProps, "Visibility", "Bool", "Bool", "true")
    return {
        "FreeCAD Origin Point Id": ReadBoxString(RecordValue["name"]),
        "FreeCAD Origin Point Label": ReadPropText(
            PointProps, "Label", "String", "String"
        ),
    }
