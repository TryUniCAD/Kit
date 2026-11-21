from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the standalone display graph allocates its state keys from ordered names and binds the actual configuration
def MakeVisKey(
    Config: ArchiveNode,
    Names: tuple[str, ...],
    ComponentRows: list[dict[str, object]],
    ReferenceRows: list[dict[str, object]],
) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("visStateKeyData_c", 1),
        {
            "f15c": 5,
            "f158": 0,
            "f118": [
                {"key": FieldInt(Config.FieldsValue, "f08"), "value": 1, "one": 1}
            ],
            "f0f0": [
                {"id": StateKey, "name": NameValue, "f384": 0, "f394": 0, "f38c": 0}
                for StateKey, NameValue in enumerate(Names, 1)
            ],
            "comps": ComponentRows,
            "f78": ReferenceRows,
            "f88": (),
            "n": 0,
        },
    )
