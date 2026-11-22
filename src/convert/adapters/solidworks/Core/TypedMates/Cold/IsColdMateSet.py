from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ColdStreamRoles import (
    HasColdStreams,
    KColdParentStreams,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KConfigStream

# the cold profile owns these three distinct classes in their physical order
KColdMateClasses = ("moMateParallel", "moMateDistanceDim_c", "moMateCoincident")

# public inspection must retain an explicit scope without qualifying inverse publication
KColdMateScope = "cold_parallel_distance_coincident"


# the specialized group must be recognized from its actual selected configuration and cold streams
def IsColdMateSet(Native: NativeAsm, Archive: SldprtArchive) -> bool:
    if (
        Archive.format_version != 4
        or ContainerMo(Archive.streams) != 19000
        or len(Native.configurations) != 1
        or len(Native.mate_lists) != 1
    ):
        return False
    (ConfigValue,) = Native.configurations
    (ListValue,) = Native.mate_lists
    return (
        ConfigValue.configuration_id == 0
        and ConfigValue.model_id
        == ListValue.owner_definition_id
        == Native.root_definition_id
        and ListValue.stream == KConfigStream + "-MatesList"
        and ListValue.declared_count == len(KColdMateClasses)
        and tuple(Value.class_name for Value in ListValue.mates) == KColdMateClasses
        and HasColdStreams(Archive, KColdParentStreams)
    )
