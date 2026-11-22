from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Views.MakeViewNode import (
    MakeViewNode,
)
from convert.adapters.solidworks.Archive.Construction.Views.MultiplyQuat import (
    MultiplyQuat,
)
from convert.adapters.solidworks.Archive.Construction.Views.ViewPlans import KViewPlans
from convert.adapters.solidworks.Archive.Construction.Views.ViewRotation import (
    ViewRotation,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# every ordinary standard view must be constructed independently from its native plan and effective detail standard
def MakeStdViews(
    StandardValue: int, *, PlatformMath: bool = False
) -> tuple[ArchiveNode, ...]:
    if type(CastValue(object, StandardValue)) is not int or StandardValue != 1:
        raise ValueError(
            "canonical views require classified effective detail standard one"
        )
    if type(CastValue(object, PlatformMath)) is not bool:
        raise TypeError("standard view rounding mode must be explicit")
    ViewsValue: list[ArchiveNode] = []
    for IndexValue, (NameValue, PlanValue) in enumerate(KViewPlans):
        Quaternion = (0.0, 0.0, 0.0, 1.0)
        for AxisName, AngleValue in PlanValue:
            Quaternion = MultiplyQuat(
                Quaternion,
                ViewRotation(AxisName, AngleValue, PlatformMath=PlatformMath),
            )
        ViewsValue.append(MakeViewNode(NameValue, IndexValue, Quaternion))
    return tuple(ViewsValue)
