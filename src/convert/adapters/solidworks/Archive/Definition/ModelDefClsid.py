from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Definition import KAsmClsid, KPartClsid

# the serialized guid resolves the untagged outer document owner before class-specific reads
KModelDefClsids = MappingProxyType(
    {
        RuntimeClass("uiPartDoc_c", 1): KPartClsid,
        RuntimeClass("uiAssemblyDoc_c", 1): KAsmClsid,
    }
)


# the untagged definition cannot use a fallback class when the file type differs
def ReadDefClass(ClsidValue: bytes) -> RuntimeClass:
    for ClassValue, ExpectedClsid in KModelDefClsids.items():
        if ClsidValue == ExpectedClsid:
            return ClassValue
    raise BodyUnsupported("unsupported SOLIDWORKS model Definition clsid")
