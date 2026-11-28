from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.ShellStock import (
    ShellStock,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchRelation


# the relation vocabulary follows the verified native line owners and their actual point incidence
def BindShellSketch(SketchValue: Sketch, StockValue: ShellStock) -> Sketch:
    LoopValue = StockValue.LoopValue
    Directions: list[SketchRelation] = []
    Endpoints: list[list[ConstraintRef]] = [[] for _ in LoopValue.PointsValue]
    for Entity, LineValue in zip(
        SketchValue.entities, LoopValue.LinesValue, strict=True
    ):
        StartValue, EndValue = (
            LoopValue.PointsValue[LineValue.StartValue],
            LoopValue.PointsValue[LineValue.EndValue],
        )
        RelationId = Entity.id + ":direction"
        Directions.append(
            SketchRelation(
                RelationId,
                (
                    "horizontal"
                    if StartValue.PositionValue[1] == EndValue.PositionValue[1]
                    else "vertical"
                ),
                (ConstraintRef(Entity.id),),
                provenance=TypedProvenance(LoopValue.OwnerValue, RelationId),
            )
        )
        Endpoints[LineValue.StartValue].append(ConstraintRef(Entity.id, "start"))
        Endpoints[LineValue.EndValue].append(ConstraintRef(Entity.id, "end"))
    Joins = tuple(
        SketchRelation(
            f"{SketchValue.id}:join:{PointValue.CreationId}",
            "coincident",
            tuple(References),
            provenance=TypedProvenance(
                LoopValue.OwnerValue, f"point:{PointValue.CreationId}"
            ),
        )
        for PointValue, References in zip(LoopValue.PointsValue, Endpoints, strict=True)
    )
    return ReplaceValue(SketchValue, constraints=(*Directions, *Joins))
