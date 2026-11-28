from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)


# custom driver names need a bounded cold scope before the equation may claim their live owners
def HasNamedEq(NamesValue: tuple[str, str, str], Archive: SldprtArchive) -> bool:
    if NamesValue == ("D1", "D2", "D1"):
        return False
    if (
        not IsCacheAbsent(Archive)
        or NamesValue[2].casefold() == "d2"
        or len({Value.casefold() for Value in NamesValue}) != 3
        or any(not Value.isascii() or not Value.isidentifier() for Value in NamesValue)
    ):
        raise ValueError("named width depth requires distinct local cold parameters")
    return True
