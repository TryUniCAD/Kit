from typing import cast as CastValue

from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration


# implicit active selection cannot replace an actual independent authored configuration in a linked assembly bundle
def ReadAsmConfig(Document: CadDocument) -> Configuration:
    RequireAsm(
        len(Document.configurations) == 1, "one active configuration is required"
    )
    (ConfigValue,) = Document.configurations
    RequireAsm(
        type(CastValue(object, ConfigValue.active)) is bool and ConfigValue.active,
        "configuration must be explicitly active",
    )
    RequireAsm(
        ConfigValue.parent_id is None
        and not ConfigValue.overrides
        and not ConfigValue.suppressed_feature_ids
        and not ConfigValue.attributes,
        "configuration has unsupported inherited or extended state",
    )
    return ConfigValue
