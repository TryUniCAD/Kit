from typing import Sequence

from convert.adapters.solidworks.Core.NativeScalar import NativeScalar


# display copies can repeat a name while one distinct native record owns the driving value
def PickNamedScalar(Named: Sequence[NativeScalar]) -> NativeScalar | None:
    if len(Named) == 1:
        return Named[0]
    if (
        not Named
        or any(
            Item.object_id is None or Item.role not in {"display", "driving"}
            for Item in Named
        )
        or len({Item.object_id for Item in Named}) != len(Named)
    ):
        return None
    Driving = [Item for Item in Named if Item.role == "driving"]
    return Driving[0] if len(Driving) == 1 else None
