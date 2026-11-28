from convert.adapters.solidworks.Core.TypedMates.Cylinders.CanReadKinds import (
    CanReadKinds,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv


# existing readers keep ownership outside the measured flat single configuration mate profile
def CanReadMates(EnvValue: PublicMateEnv) -> bool:
    Native = EnvValue.NativeValue
    if (
        EnvValue.ArchiveValue.format_version != 4
        or ContainerMo(EnvValue.ArchiveValue.streams) != 19000
    ):
        return False
    if (
        len(Native.configurations) != 1
        or len(Native.mate_lists) != 1
        or len(Native.occurrences) < 2
    ):
        return False
    ConfigValue, ListValue = Native.configurations[0], Native.mate_lists[0]
    if (
        ConfigValue.configuration_id != 0
        or ConfigValue.model_id != Native.root_definition_id
    ):
        return False
    if (
        ListValue.owner_definition_id != Native.root_definition_id
        or ListValue.stream != "Contents/Config-0-MatesList"
    ):
        return False
    if (
        not ListValue.mates
        or ListValue.declared_count != len(ListValue.mates)
        or not CanReadKinds(tuple(Value.class_name for Value in ListValue.mates))
    ):
        return False
    Definitions = {Value.object_id: Value for Value in Native.definitions}
    if len(Definitions) != len(Native.definitions):
        return False
    return all(
        Value.owner_definition_id == Native.root_definition_id
        and Value.configuration_id == 0
        and not (Value.suppressed or Value.virtual or Value.flexible)
        and Value.definition_id in EnvValue.PathsValue
        and Value.definition_id in EnvValue.DocumentsValue
        and Value.definition_id in Definitions
        and Definitions[Value.definition_id].document_type == "PART"
        for Value in Native.occurrences
    ) and all(
        Value.document_type == "PART" or Value.object_id == Native.root_definition_id
        for Value in Native.definitions
    )
