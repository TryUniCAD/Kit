from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop


# analytic stock and neutral sketch projection retain the same checked loop and editable depth
@Dataclass(frozen=True, slots=True)
class PatStock:
    OwnerValue: ExtrudeOwner
    PlanValue: PrismPlan
    LoopValue: LineLoop
