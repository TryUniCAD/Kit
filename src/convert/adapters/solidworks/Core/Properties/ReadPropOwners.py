from collections.abc import Mapping
from typing import cast as CastValue

from interchange import CadDocument


# owner tables need concrete runtime checks before optional configuration text can rely on their identities
def ReadOwnerTable(InfoObject: object) -> dict[int, str]:
    if not isinstance(InfoObject, Mapping):
        raise ValueError(
            "part configuration properties require a complete typed manager"
        )
    InfoValue = CastValue(Mapping[str, object], InfoObject)
    if InfoValue.get("status") != "complete":
        raise ValueError(
            "part configuration properties require a complete typed manager"
        )
    RowsValue = InfoValue.get("configurations")
    if not isinstance(RowsValue, (list, tuple)):
        raise ValueError("part configuration property owners are unavailable")
    OwnersValue: dict[int, str] = {}
    for RowObject in CastValue(tuple[object, ...], RowsValue):
        if not isinstance(RowObject, Mapping):
            raise ValueError("part configuration property owner is malformed")
        RowValue = CastValue(Mapping[str, object], RowObject)
        IdentValue, NameValue = RowValue.get("native_object_id"), RowValue.get("name")
        if (
            type(IdentValue) is not int
            or not isinstance(NameValue, str)
            or IdentValue in OwnersValue
        ):
            raise ValueError("part configuration property owner identity is ambiguous")
        OwnersValue[IdentValue] = NameValue
    return OwnersValue


# configuration xml ids must resolve to the same actual manager node and named neutral configuration
def ReadPropOwners(Document: CadDocument) -> dict[int, str]:
    OwnersValue = ReadOwnerTable(
        Document.metadata.get("solidworks.typed_configuration_manager")
    )
    NeutralOwners: dict[int, str] = {}
    for ConfigValue in Document.configurations:
        IdentValue = ConfigValue.attributes.get("native_configuration_id")
        if type(IdentValue) is not int or IdentValue in NeutralOwners:
            raise ValueError(
                "part configuration property neutral identity is ambiguous"
            )
        NeutralOwners[IdentValue] = ConfigValue.name
    if NeutralOwners != OwnersValue:
        raise ValueError(
            "part configuration property owners differ from the actual manager"
        )
    return OwnersValue
