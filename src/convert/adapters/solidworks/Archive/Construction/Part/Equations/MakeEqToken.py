from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# equation token ownership requires offsets within each side and the corresponding native token colour
def MakeEqToken(
    ClassName: str,
    TokenText: str,
    StartValue: int,
    KindValue: int,
    **FieldsValue: object,
) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass(ClassName, 1),
        {
            **FieldsValue,
            "f08": TokenText,
            "f10": 1 if KindValue == 0 else 8,
            "f14": StartValue,
            "f18": StartValue + len(TokenText),
            "f1c": KindValue,
        },
    )
