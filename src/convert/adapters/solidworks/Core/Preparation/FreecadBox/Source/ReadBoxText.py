from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.MakeFcDocText import (
    MakeFcDocText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxUnits import (
    ReadBoxUnits,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    RequireEmpty,
    RequireProp,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KDimensions,
    KDocProps,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.Records.RecordSource import CadSource


# supported metadata must keep the source document framing and exact authored property inventory
def ReadDocProps(
    Source: CadSource,
    Document: Mapping[str, object],
    Release: str,
) -> dict[str, Mapping[str, object]]:
    Fields = {
        "document_properties",
        "entry_order",
        "file_version",
        "objects",
        "program_version",
        "schema_version",
    }
    if Release != "0.21":
        Fields.add("string_hasher")
    RequireBox(
        set(Document) == Fields,
        "FreeCAD document carries a different source state inventory",
    )
    RequireBox(
        Document["program_version"] == Source.application_version
        and Document["file_version"] == Source.container_version
        and Document["schema_version"] == Source.attributes["freecad_schema_version"],
        "FreeCAD document and source version owners disagree",
    )
    Records = NativeRows(NativeRecord(Document["document_properties"])["children"])
    Properties = {
        ReadBoxString(NativeRecord(RecordValue["attributes"])["name"]): RecordValue
        for RecordValue in Records
    }
    Expected = (
        KDocProps if Release == "0.21" else KDocProps | {"UnitSystem", "UseHasher"}
    )
    RequireBox(
        len(Properties) == len(Records) and frozenset(Properties) == Expected,
        "FreeCAD source document contains an unqualified property set",
    )
    for NameValue in ("FileName", "Tip", "TransientDir"):
        RecordValue = Properties[NameValue]
        RequireBox(
            RecordValue["tag"] == "_Property" and "children" not in RecordValue,
            "FreeCAD transient document property has actual authored content",
        )
    for NameValue in ("Material", "Meta"):
        RequireEmpty(Properties, NameValue, "Map", "Map")
    RequireProp(Properties, "ShowHidden", "Bool", "Bool", "false")
    return Properties


# literal source properties and units must survive separately from the derived model shape
def ReadBoxText(
    Source: CadSource,
    Document: Mapping[str, object],
    Release: str,
    BodyName: str,
    FeatureId: str,
    DriverIds: tuple[str, str, str],
    Flags: Mapping[str, str],
) -> tuple[str, PartTextInput, int, UnitInput | None]:
    Properties = ReadDocProps(Source, Document, Release)
    Summary, Extra, Creation = MakeFcDocText(
        Source,
        Properties,
        {"FreeCAD Body Label": BodyName, "FreeCAD Feature Id": FeatureId},
    )
    Extra.update(
        {
            "FreeCAD " + NameValue + " Parameter": Driver
            for NameValue, Driver in zip(KDimensions, DriverIds, strict=True)
        }
    )
    Units: UnitInput | None = None
    if Release != "0.21":
        Units, Preferences = ReadBoxUnits(Document, Properties)
        Extra.update(Preferences)
    Extra.update(Flags)
    return Summary["title"], PartTextInput(Summary, Extra, {}), Creation, Units
