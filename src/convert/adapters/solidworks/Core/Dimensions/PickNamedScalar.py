from typing import Sequence

from convert.adapters.solidworks.Core.NativeScalar import NativeScalar


# display copies can repeat a name while one distinct native record owns the driving value
def PickNamedScalar(Named: Sequence[NativeScalar]) -> NativeScalar | None:
    if len(Named) == 1:
        return Named[0]
    if (
        not Named
        or any(
            ItemValue.object_id is None or ItemValue.role not in {"display", "driving"}
            for ItemValue in Named
        )
        or len({ItemValue.object_id for ItemValue in Named}) != len(Named)
    ):
        return None
    Driving = [ItemValue for ItemValue in Named if ItemValue.role == "driving"]
    return Driving[0] if len(Driving) == 1 else None
