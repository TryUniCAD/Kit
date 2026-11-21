from collections.abc import Mapping
from datetime import datetime as DateTime
from uuid import UUID

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxUnits import (
    ReadBoxUnits,
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


# source identity and both dates must come from literal fields with explicit time zones
def ReadBoxIdentity(
    Properties: Mapping[str, object],
    RawText: Mapping[str, str],
) -> tuple[str, int]:
    UidValue = ReadPropText(Properties, "Uid", "UUID", "Uuid")
    RequireBox(
        str(UUID(UidValue)) == UidValue,
        "FreeCAD source identity is outside the measured UUID form",
    )
    Created = DateTime.fromisoformat(RawText["CreationDate"])
    Modified = DateTime.fromisoformat(RawText["LastModifiedDate"])
    RequireBox(
        Created.tzinfo is not None and Modified.tzinfo is not None,
        "FreeCAD authored dates must be explicit",
    )
    return UidValue, int(Created.timestamp())


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
    Names = (
        "Comment",
        "Company",
        "CreatedBy",
        "CreationDate",
        "Id",
        "Label",
        "LastModifiedBy",
        "LastModifiedDate",
        "License",
        "LicenseURL",
        "TipName",
    )
    RawText = {
        NameValue: ReadPropText(Properties, NameValue, "String", "String")
        for NameValue in Names
    }
    RequireBox(
        RawText["Label"] and not RawText["TipName"],
        "FreeCAD source has no label or has an unsupported document tip",
    )
    UidValue, Creation = ReadBoxIdentity(Properties, RawText)
    Summary = {
        Caption: RawText[NameValue]
        for NameValue, Caption in (
            ("Label", "title"),
            ("Comment", "comments"),
            ("CreatedBy", "author"),
        )
        if RawText[NameValue]
    }
    Extra = {
        "FreeCAD " + NameValue: RawText[NameValue]
        for NameValue in (
            "Company",
            "CreationDate",
            "Id",
            "LastModifiedBy",
            "LastModifiedDate",
            "License",
            "LicenseURL",
        )
        if RawText[NameValue]
    }
    Extra.update(
        {
            "FreeCAD Uid": UidValue,
            "FreeCAD Body Label": BodyName,
            "FreeCAD Feature Id": FeatureId,
            "FreeCAD Source Version": Source.application_version,
            "FreeCAD Source Schema": ReadBoxString(Document["schema_version"]),
            "FreeCAD Show Hidden": "false",
        }
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
    return RawText["Label"], PartTextInput(Summary, Extra, {}), Creation, Units
