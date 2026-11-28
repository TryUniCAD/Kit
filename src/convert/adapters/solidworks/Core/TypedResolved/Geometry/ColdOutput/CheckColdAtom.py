from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState


# constructor body free state must remain explicit so stale kernel ownership cannot gain inferred geometry
def CheckColdAtom(AtomValue: ArchiveNode, *, ImplicitName: bool = False) -> None:
    FieldsValue = AtomValue.FieldsValue
    Expected = {
        "f08": -1,
        "f0c": 1,
        "f28": 0x40000000,
        "f2c": 0,
        "f20": "",
        "has_list68": 0,
        "f78": None,
        "f144": 0,
        "f158": 0,
        "body_kind": 0,
        "f170": 0,
        "f18c": int(ImplicitName),
        "f198": -1,
        "f180": 0,
        "f188": 0,
        "f1b0": 0,
        "f19c": 6,
    }
    if any(
        FieldsValue.get(NameValue) != ValueData
        for NameValue, ValueData in Expected.items()
    ):
        raise ValueError("cold name has alternate node body tag or display state")
    if (
        "f160" in FieldsValue
        or "f120" in FieldsValue
        or (ImplicitName and FieldsValue.get("f18") is not None)
        or not IsLineState(FieldsValue.get("f60"))
    ):
        raise ValueError(
            "cold atom contains an embedded body or additional concept state"
        )
