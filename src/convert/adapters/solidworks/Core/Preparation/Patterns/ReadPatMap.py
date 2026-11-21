from typing import TypeVar

from interchange.document.Models.DocumentIdentity import Identified

# each model collection keeps its concrete type while joining through portable identifiers
KPatMember = TypeVar("KPatMember", bound=Identified)


# a reference must never resolve through an absent or ambiguous owner identity
def ReadPatMap(Values: tuple[KPatMember, ...]) -> dict[str, KPatMember]:
    Members = {ItemValue.id: ItemValue for ItemValue in Values}
    if len(Members) != len(Values) or any(
        type(Identity) is not str or not Identity.strip() for Identity in Members
    ):
        raise ValueError("neutral owner IDs are missing or ambiguous")
    return Members
