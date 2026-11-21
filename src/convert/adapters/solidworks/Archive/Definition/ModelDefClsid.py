from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Definition import KAsmClsid, KPartClsid

# the untagged root has a fixed concrete identity within the ordinary part profile
KPartDefClass = RuntimeClass("uiPartDoc_c", 1)

# the ordinary assembly clsid owns a different native settings tail
KAsmDefClass = RuntimeClass("uiAssemblyDoc_c", 1)


# the untagged definition cannot use a fallback class when the file type differs
def ReadDefClass(ClsidValue: bytes, *, Assembly: bool = False) -> RuntimeClass:
    if Assembly:
        if ClsidValue != KAsmClsid:
            raise BodyUnsupported(
                "SOLIDWORKS assembly Definition requires the ordinary assembly CLSID"
            )
        return KAsmDefClass
    if ClsidValue != KPartClsid:
        raise BodyUnsupported(
            "SOLIDWORKS part Definition requires the ordinary part CLSID"
        )
    return KPartDefClass
