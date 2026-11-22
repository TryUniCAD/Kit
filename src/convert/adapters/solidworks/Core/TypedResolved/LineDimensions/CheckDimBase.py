from collections.abc import Mapping


# linked relations with tolerance attachment suppression or alternative drive modes require separate semantic admission
def CheckDimBase(FieldsValue: Mapping[str, object]) -> None:
    if (
        any(FieldsValue.get(NameValue) is not None for NameValue in ("f48", "f60"))
        or any(
            FieldsValue.get(NameValue) != 0
            for NameValue in ("f54", "f5c", "f68", "has_f78", "f94", "f98")
        )
        or FieldsValue.get("f90") != 2
    ):
        raise ValueError("typed rectangle dimension has an unsupported drive mode")
