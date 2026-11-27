from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv


# strict reads recognize the owned planar list independently of component eligibility
def HasPlanarMates(EnvValue: PublicMateEnv) -> bool:
    Native = EnvValue.NativeValue
    if (
        EnvValue.ArchiveValue.format_version != 4
        or ContainerMo(EnvValue.ArchiveValue.streams) != 19000
        or len(Native.configurations) != 1
        or len(Native.mate_lists) != 1
    ):
        return False
    ConfigValue, ListValue = Native.configurations[0], Native.mate_lists[0]
    return (
        ConfigValue.configuration_id == 0
        and ConfigValue.model_id == Native.root_definition_id
        and ListValue.owner_definition_id == Native.root_definition_id
        and ListValue.stream == "Contents/Config-0-MatesList"
        and ListValue.declared_count == len(ListValue.mates)
        and tuple(Value.class_name for Value in ListValue.mates)
        == ("moMateCoincident", "moMateDistanceDim_c")
    )


# typed endpoints require the actual flat component files and their eligible owners
def CanReadMates(EnvValue: PublicMateEnv) -> bool:
    Native = EnvValue.NativeValue
    if not HasPlanarMates(EnvValue) or len(Native.occurrences) != 2:
        return False
    Definitions = {Value.object_id: Value for Value in Native.definitions}
    if len(Definitions) != 2 or len(Native.definitions) != 2:
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
