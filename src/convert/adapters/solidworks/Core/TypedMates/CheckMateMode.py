from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# optional mate states must not be silently represented as an ordinary active aligned relationship
def CheckMateMode(NodeValue: ArchiveNode) -> None:
    Fields = NodeValue.FieldsValue
    if FieldInt(Fields, "f3b4") != 1 or FieldInt(Fields, "f0c") not in (1, 0x100):
        raise ValueError(
            "typed mate alignment or node update word is outside the qualified profile"
        )
    if any(
        FieldInt(Fields, NameValue) != 0
        for NameValue in ("f388", "f390", "f394", "f438", "f480")
    ):
        raise ValueError("typed mate has unsupported auxiliary options")
    if any(
        Fields.get(NameValue) is not None
        for NameValue in ("f430", "f470", "f468", "f478")
    ):
        raise ValueError("typed mate has unsupported auxiliary owners")
    if ReadRows(Fields.get("f370")) or ReadRows(Fields.get("f448")):
        raise ValueError("typed mate has unsupported auxiliary records")
    if Fields.get("has_f3c0") != 0 or FieldInt(Fields, "f3b8") not in (0, 1):
        raise ValueError("typed mate has unsupported direction or solved state")
    if NodeValue.ClassValue.NameValue == "moMateDistanceDim_c" and tuple(
        FieldInt(Fields, NameValue)
        for NameValue in ("f4c0", "f4d8", "f4dc", "f4e0", "f4f4")
    ) != (1, 1, 3, 3, 0):
        raise ValueError(
            "typed distance mate mode is outside the ordinary plane profile"
        )
