from __future__ import annotations

from collections.abc import Mapping

from tools.Donors.FormatLabel import FormatLabel


def FindGrowth(
    CurrentMap: Mapping[tuple[str, str], int],
    BaselineMap: Mapping[tuple[str, str], int],
) -> list[str]:
    GrowthList: list[str] = []
    for KeyPair, CountValue in sorted(CurrentMap.items()):
        Allowed = BaselineMap.get(KeyPair)
        LabelText = FormatLabel(KeyPair)
        if Allowed is None:
            GrowthList.append(
                f"{LabelText} are new ({CountValue}); generate them instead"
            )
        elif CountValue > Allowed:
            GrowthList.append(f"{LabelText} grew from {Allowed} to {CountValue}")
    return GrowthList
