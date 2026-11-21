from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Definition import KAsmClsid, KPartClsid

# the ordinary profile binds the part identity before interpreting any of its fields
KPartDefClass = RuntimeClass("uiPartDoc_c", 1)

# the serialized guid resolves the untagged outer document owner before reads of the selected class
KModelDefClsids = MappingProxyType(
    {
        KPartDefClass: KPartClsid,
        RuntimeClass("uiAssemblyDoc_c", 1): KAsmClsid,
    }
)


# the untagged definition cannot use a fallback class when the file type differs
def ReadDefClass(ClsidValue: bytes, *, OrdinaryOnly: bool = False) -> RuntimeClass:
    if OrdinaryOnly:
        if ClsidValue != KPartClsid:
            raise BodyUnsupported(
                "SOLIDWORKS part Definition requires the ordinary part CLSID"
            )
        return KPartDefClass
    for ClassValue, ExpectedClsid in KModelDefClsids.items():
        if ClsidValue == ExpectedClsid:
            return ClassValue
    raise BodyUnsupported("unsupported SOLIDWORKS model Definition clsid")
