from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Properties.PartTextData import PartTextData
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration


# admitted property scopes attach atomically and preserve configuration identity and unrelated neutral attributes
def ApplyPartText(Document: CadDocument, TextValue: PartTextData) -> CadDocument:
    Metadata = dict(Document.metadata)
    if TextValue.SummaryFields is not None:
        Metadata["document_summary"] = TextValue.SummaryFields
    if TextValue.DocumentFields is not None:
        Metadata["custom_properties"] = TextValue.DocumentFields
    Metadata["solidworks.part_text_properties"] = {
        "status": "complete",
        "archive_version": 19000,
        "profile": "compatible_literal_text",
        "configuration_ids": tuple(TextValue.ConfigFields),
        "binary_configuration_values": "non_authoritative_cache",
        "advanced_property_owners": False,
    }
    ConfigValues: list[Configuration] = []
    for ConfigValue in Document.configurations:
        IdentValue = ConfigValue.attributes.get("native_configuration_id")
        if type(IdentValue) is int and IdentValue in TextValue.ConfigFields:
            Attributes = dict(ConfigValue.attributes)
            Attributes["custom_properties"] = TextValue.ConfigFields[IdentValue]
            ConfigValue = ReplaceValue(
                ConfigValue, attributes=FreezeMapping(Attributes)
            )
        ConfigValues.append(ConfigValue)
    return ReplaceValue(
        Document, metadata=FreezeMapping(Metadata), configurations=tuple(ConfigValues)
    )
