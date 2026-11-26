from collections.abc import Mapping, Set as SetValue

from convert.Geometry.Parasolid import LinkedOrder


# unused scanner candidates are harmless only when they cannot change selected ordering
def CheckRankRows(
    Selected: SetValue[int], Links: Mapping[int, tuple[int, int]]
) -> None:
    if Links.keys() <= Selected:
        return
    Owned = {
        IndexValue: Links[IndexValue] for IndexValue in Selected if IndexValue in Links
    }
    if LinkedOrder(Selected, Links) != LinkedOrder(Selected, Owned):
        raise ValueError("unowned scanner rows influence selected topology order")
