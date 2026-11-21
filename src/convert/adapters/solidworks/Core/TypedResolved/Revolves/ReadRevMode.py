from collections.abc import Mapping


# modern end words and actual secondary ownership distinguish the witnessed sweep modes
def ReadRevMode(FieldsValue: Mapping[str, object]) -> str:
    WordsValue = tuple(
        FieldsValue.get(NameValue) for NameValue in ("f08", "f0c", "f10")
    )
    if (
        any(
            FieldsValue.get(NameValue) != 0
            for NameValue in ("f138", "f13c", "f140", "f144")
        )
        or any(
            FieldsValue.get(NameValue) is not None
            for NameValue in ("f118", "f120", "f128", "f130", "f28", "f30")
        )
        or "f20" not in FieldsValue
    ):
        raise ValueError("ordinary revolve alternate angular end state is unqualified")
    HasAgainst = FieldsValue["f20"] is not None
    if WordsValue == (1, 0, 0) and not HasAgainst:
        return "one_sided"
    if WordsValue == (0, 6, 0) and not HasAgainst:
        return "symmetric_full"
    if WordsValue == (0, 0, 0) and HasAgainst:
        return "two_sided"
    raise ValueError("ordinary revolve angular end words and secondary owner disagree")
