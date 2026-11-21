from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING
from convert.adapters.solidworks.Core.NativeDimension import NativeDimension

from interchange.geometry.Models.Sketch import ConstraintRef as RuleRef
from convert.adapters.solidworks.Core.Dimensions.RadialTarget import RadialTarget

if TYPE_CHECKING:
    from convert.adapters.solidworks.Core.Dimensions.RuleContext import RuleContext
    from convert.adapters.solidworks.Core.Records.NativeRule import NativeRule


# native circle operands and rectangle measurements need distinct reference binding rules
def BindRuleRefsMut(
    RuleValue: NativeRule,
    RefMap: Mapping[str, str],
    ContextMut: RuleContext,
    Dimension: NativeDimension | None,
    Dimensions: Sequence[NativeDimension],
) -> tuple[list[RuleRef], str]:
    Points = RuleValue.reference_points or ("",) * len(RuleValue.references)
    References: list[RuleRef] = []
    for NativeRef, PointName in zip(RuleValue.references, Points, strict=True):
        Resolved = RefMap.get(NativeRef)
        if not Resolved:
            References.clear()
            break
        References.append(RuleRef(Resolved, PointName))
    KindValue = RuleValue.kind
    Radial = Dimension is not None and Dimension.kind in {"diameter", "radius"}
    if not References and Radial and Dimension is not None and len(Dimensions) == 1:
        CircleId = RadialTarget(Dimension, RuleValue, ContextMut.MarkerCircles)
        if CircleId is not None:
            References = [RuleRef(CircleId)]
            KindValue = Dimension.kind
    if (
        not References
        and not Radial
        and RuleValue.parameter is not None
        and Dimension is not None
        and Dimension.value_mm is not None
    ):
        KeyValue = round(Dimension.value_mm, 9)
        Available = ContextMut.Candidates.get(KeyValue, [])
        if Available:
            Index = ContextMut.DimensionUsage[KeyValue] % len(Available)
            EntityId, KindValue = Available[Index]
            ContextMut.DimensionUsage[KeyValue] += 1
            References = [RuleRef(EntityId)]
    return References, KindValue
