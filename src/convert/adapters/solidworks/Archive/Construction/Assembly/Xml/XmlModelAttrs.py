from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# model index identities use their actual configuration local namespace file binding and current target stamp while preserving native signed flags rendering
def XmlModelAttrs(
    ConfigValue: ArchiveNode,
    DocumentId: int,
    FileId: int,
    NameValue: str,
    StampValue: int,
) -> dict[str, str]:
    FlagsValue = FieldInt(ConfigValue.FieldsValue, "f4c4")
    SignedFlags = FlagsValue - (1 << 32) if FlagsValue & (1 << 31) else FlagsValue
    return {
        "id": str(DocumentId),
        "swName": NameValue,
        "swConfigurationName": ReadNodeName(ConfigValue),
        "swConfigurationId": str(ConfigValue.FieldsValue["f08"]),
        "swLastModifiedStamp": str(StampValue),
        "swConfigurationFlags": str(SignedFlags),
        "swFileRef": str(FileId),
    }
