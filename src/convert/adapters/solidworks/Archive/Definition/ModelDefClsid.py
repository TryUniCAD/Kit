from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Definition import KAsmClsid, KPartClsid

# the ordinary profile binds the part identity before interpreting any of its fields
KPartDefClass = RuntimeClass("uiPartDoc_c", 1)

# the ordinary assembly clsid owns the separate native settings tail
KAsmDefClass = RuntimeClass("uiAssemblyDoc_c", 1)

# the serialized guid resolves the untagged outer document owner before reads of the selected class
KModelDefClsids = MappingProxyType(
    {
        KPartDefClass: KPartClsid,
        KAsmDefClass: KAsmClsid,
    }
)


# the untagged definition cannot use a fallback class when the file type differs
def ReadDefClass(
    ClsidValue: bytes, *, OrdinaryOnly: bool = False, Assembly: bool = False
) -> RuntimeClass:
    if Assembly or OrdinaryOnly:
        ClassValue = KAsmDefClass if Assembly else KPartDefClass
        if ClsidValue != KModelDefClsids[ClassValue]:
            KindValue = "assembly" if Assembly else "part"
            raise BodyUnsupported(
                f"SOLIDWORKS {KindValue} Definition requires the ordinary {KindValue} CLSID"
            )
        return ClassValue
    for ClassValue, ExpectedClsid in KModelDefClsids.items():
        if ClsidValue == ExpectedClsid:
            return ClassValue
    raise BodyUnsupported("unsupported SOLIDWORKS model Definition clsid")
