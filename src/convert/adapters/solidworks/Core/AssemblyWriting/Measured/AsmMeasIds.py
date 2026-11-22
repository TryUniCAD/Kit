from collections.abc import Mapping

from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAsmPlan,
)


# original author ids are not encoded so a reopened bundle joins the immutable receipt aliases by its measured member order
def AsmMeasIds(
    PlanValue: NestedAsmPlan, MemberRows: tuple[dict[str, object], ...], Reopened: bool
) -> Mapping[str, str]:
    Definitions = PlanValue.OrderedDefinitions
    if not Reopened:
        return {Value.id: Value.id for Value in Definitions}
    Values: dict[str, str] = {}
    for Definition, RowValue in zip(Definitions, MemberRows, strict=True):
        Identity = RowValue.get("id")
        if type(Identity) is not str or not Identity:
            raise ValueError(
                "reopened assembly measurement has an invalid member identity"
            )
        Values[Definition.id] = Identity
    if len(set(Values.values())) != len(Definitions):
        raise ValueError(
            "reopened assembly measurement has duplicate member identities"
        )
    return Values
