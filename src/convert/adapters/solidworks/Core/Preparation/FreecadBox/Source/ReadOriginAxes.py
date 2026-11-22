from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxOriginAxes import (
    BoxOriginAxes,
    BoxOriginAxis,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadAxisPlace import (
    ReadAxisPlace,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxOrigin import (
    CheckOrigLinks,
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
from interchange.geometry.Models.Transform import KAxisX, KAxisY, KAxisZ

# roles ordered by the actual origin links identify the three independently placed axes
KOriginDirs = {"X_Axis": KAxisX, "Y_Axis": KAxisY, "Z_Axis": KAxisZ}


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
        LabelValue.strip() and LabelValue.isprintable(), "FreeCAD datum label is invalid"
    )
    return LabelValue


# foreign roles or extra source functionality cannot be treated as a default axis
def ReadAxisOwner(Record: Mapping[str, object], RoleName: str) -> BoxOriginAxis:
    Properties = NativeRecord(Record["properties"])
    RequireBox(
        Record["type_id"] == "App::Line"
        and not (
            Record["touched"]
            or Record["dependencies"]
            or Record["extensions"]
            or Record["transient_properties"]
        )
        and set(Properties)
        == {"ExpressionEngine", "Label", "Label2", "Placement", "Role", "Visibility"},
        "FreeCAD origin axis has an unrepresented owner or property",
    )
    RequireEmpty(Properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    RequireProp(Properties, "Role", "String", "String", RoleName)
    return BoxOriginAxis(
        ReadBoxString(Record["object_id"]),
        RoleName,
        ReadAxLabel(Properties),
        ReadAxisPlace(Properties, KOriginDirs[RoleName]),
        IsAxisShown(Properties),
    )


# the whole ordinary origin owns the real signed line directions and their distinct identifiers
def ReadOriginAxes(Document: CadDocument) -> BoxOriginAxes:
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
    RequireBox(
        Origin["type_id"] == "App::Origin"
        and set(Properties)
        == {"ExpressionEngine", "Label", "Label2", "OriginFeatures", "Visibility"},
        "FreeCAD origin has an unrepresented owner or property",
    )
    CheckOrigLinks(Origin, Properties, "0.21")
    RequireEmpty(Properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    return BoxOriginAxes(
        ReadBoxString(Origin["object_id"]),
        ReadAxLabel(Properties),
        IsAxisShown(Properties),
        tuple(ReadAxisOwner(Objects[RoleName], RoleName) for RoleName in KOriginDirs),
    )
