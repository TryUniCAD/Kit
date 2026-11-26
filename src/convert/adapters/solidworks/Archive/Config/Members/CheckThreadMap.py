from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# populated holder rows remain unqualified even when their links reuse already mapped objects
def CheckThreadMap(RootValue: ArchiveNode) -> None:
    if RootValue.FieldsValue["n"] != 0:
        raise BodyUnsupported(
            "populated SOLIDWORKS thread reference maps are unqualified"
        )
