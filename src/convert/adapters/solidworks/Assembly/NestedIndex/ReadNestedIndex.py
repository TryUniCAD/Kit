from collections.abc import Mapping

from convert.adapters.solidworks.Assembly.Assembly import NativeAsm, NativeAsmItem
from convert.adapters.solidworks.Assembly.NestedIndex.IndexModel import IndexModel
from convert.adapters.solidworks.Assembly.NestedIndex.ReadIndexModel import (
    ReadIndexModel,
)
from convert.adapters.solidworks.Assembly.NestedIndex.ReadIndexOrders import (
    ReadIndexOrders,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive


# publish the physical titles and local orders only after the entire selected definition graph agrees
def ReadNestedIndex(
    Archive: SldprtArchive, Native: NativeAsm, SourceData: Mapping[int, object]
) -> tuple[dict[int, str], dict[int, int]]:
    RootId = Native.root_definition_id
    Files = {Value.object_id: Value for Value in Native.files}
    Definitions = {Value.object_id: Value for Value in Native.definitions}
    Models: dict[int, IndexModel] = {}
    Members: dict[int, list[NativeAsmItem]] = {}
    for Definition in Native.definitions:
        Identity = Definition.object_id
        Physical = Archive
        if Identity != RootId:
            RawValue = SourceData.get(Identity)
            if not isinstance(RawValue, bytes):
                raise ValueError("nested index lacks an owned physical child")
            Physical = SldprtArchive.from_bytes(RawValue)
        Models[Identity] = ReadIndexModel(
            Physical, Definition, Files[Definition.file_id]
        )
        Members[Identity] = []
    if (
        len(Definitions) != len(Native.definitions)
        or len(Files) != len(Native.files)
        or len({Value.KeyValue for Value in Models.values()}) != len(Models)
        or Models[RootId].NameValue != Native.name
    ):
        raise ValueError("nested index definition identities differ or collide")
    for ItemValue in Native.occurrences:
        Definition = Definitions[ItemValue.definition_id]
        if (
            ItemValue.virtual
            or ItemValue.suppressed
            or ItemValue.flexible
            or ItemValue.configuration_id != Definition.configuration_id
            or ItemValue.configuration_name != Definition.configuration_name
        ):
            raise ValueError("nested occurrence has an unsupported target selection")
        Members[ItemValue.owner_definition_id].append(ItemValue)
    Orders: dict[int, int] = {}
    for Identity, RowsValue in Members.items():
        Orders.update(ReadIndexOrders(Models[Identity], tuple(RowsValue), Models))
    if len(Orders) != len(Native.occurrences):
        raise ValueError("nested assembly index occurrence identities collide")
    return (
        {
            Identity: Models[Identity].NameValue
            for Identity, Definition in Definitions.items()
            if Definition.name == Native.name
        },
        Orders,
    )
