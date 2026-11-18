from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceLine import (
    SourceLine,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceLine import (
    ReadSourceLine,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceRules import (
    ReadSourceRules,
)
from interchange.geometry.Models.Sketch import Sketch


# a canonical fresh contour needs an explicit reversible correspondence to every actual source line and relation
def MapSourceLines(
    SketchValue: Sketch,
    VerticesValue: tuple[tuple[float, float], ...],
    UnitScale: float,
) -> tuple[SourceLine, ...]:
    Entities = {
        frozenset(ReadSourceLine(Value, UnitScale)): Value
        for Value in SketchValue.entities
    }
    RulesValue = ReadSourceRules(SketchValue)
    if len(Entities) != 4:
        raise ValueError("source stock line geometry is duplicated or incomplete")
    Result: list[SourceLine] = []
    for Index, StartValue in enumerate(VerticesValue):
        EndValue = VerticesValue[(Index + 1) % len(VerticesValue)]
        Entity = Entities.get(frozenset((StartValue, EndValue)))
        if Entity is None:
            raise ValueError("source stock is not the actual complete rectangle")
        AxisKind = "vertical" if StartValue[0] == EndValue[0] else "horizontal"
        Relation = RulesValue[Entity.id]
        if Relation.kind != AxisKind:
            raise ValueError("source unary relation disagrees with its actual line")
        Result.append(
            SourceLine(
                Entity.id,
                Index,
                ReadSourceLine(Entity, UnitScale)[0] != StartValue,
                Relation.id,
                AxisKind,
            )
        )
    return tuple(Result)
