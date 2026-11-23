from convert.adapters.solidworks.Assembly.Assembly import NativeAsm
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ColdStreamRoles import (
    HasColdStreams,
    KColdParentStreams,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive


# the measured pair has its own complete cold stream inventory and ordered mate owners
def IsColdPair(Native: NativeAsm, Archive: SldprtArchive) -> bool:
    if (
        Archive.format_version != 4
        or ContainerMo(Archive.streams) != 19000
        or not HasColdStreams(Archive, KColdParentStreams | {"Contents/CMgrHdr2"})
        or len(Native.configurations) != 1
        or len(Native.mate_lists) != 1
    ):
        return False
    (Configuration,) = Native.configurations
    (ListValue,) = Native.mate_lists
    return (
        Configuration.configuration_id == 0
        and Configuration.model_id
        == ListValue.owner_definition_id
        == Native.root_definition_id
        and ListValue.stream == "Contents/Config-0-MatesList"
        and ListValue.declared_count == 2
        and tuple(Value.class_name for Value in ListValue.mates)
        == ("moMateCoincident", "moMateDistanceDim_c")
    )
