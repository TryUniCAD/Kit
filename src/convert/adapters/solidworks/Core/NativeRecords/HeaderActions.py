from collections.abc import Callable
from struct import unpack_from as UnpackFrom

from convert.adapters.solidworks.Container.Container import SldprtFormatError


# legacy header iteration needs one action validator without duplicating its existing cursor behavior
def ReadHdrAction(
    DataValue: bytes,
    Offset: int,
    ActionIndex: int,
    ReadString: Callable[[bytes, int], tuple[str, int]],
) -> int:
    if DataValue[Offset : Offset + 2] != bytes.fromhex("0a80"):
        raise SldprtFormatError("native SOLIDWORKS header layout is unexpected")
    Offset += 2
    StoredIndex = UnpackFrom("<I", DataValue, Offset)[0]
    if StoredIndex != ActionIndex:
        raise SldprtFormatError("native SOLIDWORKS header action index is invalid")
    Offset += 10
    ActionName, Offset = ReadString(DataValue, Offset)
    if ActionName not in {"Created", "Modified"}:
        raise SldprtFormatError("native SOLIDWORKS header action name is invalid")
    return Offset
