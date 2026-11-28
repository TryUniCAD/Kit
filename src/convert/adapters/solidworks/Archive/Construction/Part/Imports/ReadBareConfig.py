from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration


# the local import owns exactly one active root configuration without secondary state
def ReadBareConfig(DocumentValue: CadDocument) -> Configuration:
    if len(DocumentValue.configurations) != 1:
        raise ValueError("bare local import requires one selected configuration")
    (ConfigValue,) = DocumentValue.configurations
    if (
        type(ConfigValue) is not Configuration
        or type(ConfigValue.id) is not str
        or not ConfigValue.id.strip()
        or ConfigValue.active is not True
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
    ):
        raise ValueError(
            "bare local import configuration differs from its neutral owner"
        )
    return ConfigValue
