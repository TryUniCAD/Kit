from collections.abc import Mapping
from datetime import datetime as DateTime
from uuid import UUID

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropText,
)
from interchange.Records.RecordSource import CadSource


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


# document text has the same source owner for sketches and primitive based parts
def MakeFcDocText(
    Source: CadSource,
    Properties: Mapping[str, object],
    OwnerText: Mapping[str, str],
) -> tuple[dict[str, str], dict[str, str], int]:
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
    Extra["FreeCAD Uid"] = UidValue
    Extra.update(OwnerText)
    Extra.update(
        {
            "FreeCAD Source Version": Source.application_version,
            "FreeCAD Source Schema": ReadBoxString(
                Source.attributes["freecad_schema_version"]
            ),
            "FreeCAD Show Hidden": "false",
        }
    )
    return Summary, Extra, Creation
