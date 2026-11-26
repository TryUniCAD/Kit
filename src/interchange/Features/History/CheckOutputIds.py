from typing import cast as CastValue


# feature outputs must be explicit stable identities before downstream body lineage can trust them
def CheckOutputIds(Value: object) -> None:
    if not isinstance(Value, tuple):
        raise ValueError("feature output body ids must be an immutable tuple")
    IdValues = CastValue(tuple[object, ...], Value)
    if not all(
        isinstance(Identity, str) and Identity.strip() for Identity in IdValues
    ) or len(set(IdValues)) != len(IdValues):
        raise ValueError("feature output body ids must be distinct nonempty identities")
