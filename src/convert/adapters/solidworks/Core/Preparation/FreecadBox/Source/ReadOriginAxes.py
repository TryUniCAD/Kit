from collections.abc import Mapping
from math import isclose as IsClose

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxOriginAxes import (
    BoxOriginAxes,
    BoxOriginAxis,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadAxisPlace import (
    ReadAxisFrame,
    ReadAxisPlace,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxOrigin import (
    ReadBoxOrigin,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxRelease import (
    ReadBoxRelease,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropText,
    RequireEmpty,
    RequireProp,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Transform import KAxisX, KAxisY, KAxisZ, KOriginZero

# roles ordered by the actual origin links identify the three independently placed axes
KOriginDirs = {"X_Axis": KAxisX, "Y_Axis": KAxisY, "Z_Axis": KAxisZ}

# the newer geometric feature saves only the status of its transient element map version
KAxisTransient = {
    "tag": "_Property",
    "attributes": {
        "name": "_ElementMapVersion",
        "type": "App::PropertyString",
        "status": "234881024",
    },
}


# the native model visibility property cannot stand in for an absent view provider
def IsAxisShown(Properties: Mapping[str, object]) -> bool:
    Shown = ReadPropText(Properties, "Visibility", "Bool", "Bool")
    RequireBox(Shown in ("true", "false"), "FreeCAD origin visibility is malformed")
    return Shown == "true"


# the archive label remains available independently of the canonical object role
def ReadAxLabel(Properties: Mapping[str, object]) -> str:
    RequireProp(Properties, "Label2", "String", "String", "")
    LabelValue = ReadPropText(Properties, "Label", "String", "String")
    RequireBox(
        LabelValue.strip() and LabelValue.isprintable(),
        "FreeCAD datum label is invalid",
    )
    return LabelValue


# the two principal datum kinds share the same placed source property profile
def ReadDatumProps(
    Record: Mapping[str, object], RoleName: str, ClassName: str, Release: str
) -> Mapping[str, object]:
    Properties = NativeRecord(Record["properties"])
    Transients = NativeRows(Record["transient_properties"])
    RequireBox(
        Record["type_id"] == ClassName
        and not (Record["touched"] or Record["dependencies"] or Record["extensions"])
        and Transients == ((KAxisTransient,) if Release == "1.1" else ())
        and set(Properties)
        == {"ExpressionEngine", "Label", "Label2", "Placement", "Role", "Visibility"},
        "FreeCAD origin datum has an unrepresented owner or property",
    )
    RequireEmpty(Properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    RequireProp(Properties, "Role", "String", "String", RoleName)
    return Properties


# foreign roles or extra source functionality cannot be treated as a default axis
def ReadAxisOwner(
    Record: Mapping[str, object], RoleName: str, Release: str
) -> BoxOriginAxis:
    Properties = ReadDatumProps(Record, RoleName, "App::Line", Release)
    return BoxOriginAxis(
        ReadBoxString(Record["object_id"]),
        RoleName,
        ReadAxLabel(Properties),
        ReadAxisPlace(Properties, KOriginDirs[RoleName]),
        IsAxisShown(Properties),
    )


# the original signed plane placements must agree with the target principal supports
def CheckOrigPlanes(Objects: Mapping[str, Mapping[str, object]], Release: str) -> None:
    for NameValue, Direction in (
        ("XY", (0.0, 0.0, 1.0)),
        ("XZ", (0.0, -1.0, 0.0)),
        ("YZ", (1.0, 0.0, 0.0)),
    ):
        RoleName = NameValue + "_Plane"
        Properties = ReadDatumProps(Objects[RoleName], RoleName, "App::Plane", Release)
        Frame = ReadAxisFrame(Properties)
        Normal = Frame.z_axis
        RequireBox(
            Frame.origin == KOriginZero
            and ReadAxLabel(Properties) == NameValue + "-plane"
            and IsAxisShown(Properties)
            and all(
                IsClose(Value, Expected, rel_tol=0.0, abs_tol=1e-14)
                for Value, Expected in zip(
                    (Normal.x, Normal.y, Normal.z), Direction, strict=True
                )
            ),
            "FreeCAD origin plane no longer matches its signed principal support",
        )


# the whole ordinary origin owns the real signed line directions and their distinct identifiers
def ReadOriginAxes(
    Document: CadDocument, *, CheckPlanes: bool = False
) -> BoxOriginAxes:
    Release = ReadBoxRelease(Document.source.application_version)
    RootValue = NativeRecord(Document.metadata["freecad"])
    RowsValue = NativeRows(RootValue["objects"])
    Objects = {ReadBoxString(Record["name"]): Record for Record in RowsValue}
    RecordIds = tuple(ReadBoxString(Record["object_id"]) for Record in RowsValue)
    RequireBox(
        len(Objects) == len(RowsValue) == len(set(RecordIds))
        and all(
            KeyValue.isascii() and KeyValue.isdecimal() and not KeyValue.startswith("0")
            for KeyValue in RecordIds
        ),
        "FreeCAD origin requires distinct native object identities",
    )
    Origin = Objects["Origin"]
    Properties = NativeRecord(Origin["properties"])
    Expected = {"ExpressionEngine", "Label", "Label2", "OriginFeatures", "Visibility"}
    if Release == "1.1":
        Expected.add("Placement")
        RequireBox(
            Objects["Origin001"]["type_id"] == "App::Point",
            "FreeCAD origin point has a foreign owner",
        )
    RequireBox(
        Origin["type_id"] == "App::Origin" and set(Properties) == Expected,
        "FreeCAD origin has an unrepresented owner or property",
    )
    _ = ReadBoxOrigin(Objects, Release)
    if CheckPlanes:
        CheckOrigPlanes(Objects, Release)
    RequireEmpty(Properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    return BoxOriginAxes(
        ReadBoxString(Origin["object_id"]),
        ReadAxLabel(Properties),
        IsAxisShown(Properties),
        tuple(
            ReadAxisOwner(Objects[RoleName], RoleName, Release)
            for RoleName in KOriginDirs
        ),
    )
