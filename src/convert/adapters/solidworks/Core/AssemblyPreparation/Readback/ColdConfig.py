from dataclasses import replace as ReplaceValue

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration


# the index and the physically reopened member must identify the same selected configuration
def ColdConfig(Definition: ComponentDef, Document: CadDocument) -> Configuration:
    if len(Document.configurations) != 1:
        raise ValueError("reopened nested member requires a single configuration")
    (Value,) = Document.configurations
    Identity = Value.attributes.get("native_configuration_id")
    if (
        type(Identity) is not int
        or Identity != 0
        or Definition.configuration_id != str(Identity)
        or Definition.configuration_name != Value.name
        or not Value.active
    ):
        raise ValueError(
            "reopened nested member disagrees with its selected configuration"
        )
    return ReplaceValue(Value, attributes=FreezeMapping())
