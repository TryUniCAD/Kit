from collections.abc import Mapping


# unmodeled construction direction and external ownership must preserve the existing reader representation
def CheckLineEntity(
    FieldsValue: Mapping[str, object], *, SavedLine: bool = False
) -> None:
    if (
        FieldsValue.get("ext") is not None
        or FieldsValue.get("group") is not None
        or FieldsValue.get("has_name") != 0
        or FieldsValue.get("dflt") != 0
        or FieldsValue.get("f20") != int(SavedLine)
        or FieldsValue.get("f54") != 4
        or FieldsValue.get("f56") != 0
    ):
        raise ValueError("typed line ring has unqualified entity ownership or geometry")
