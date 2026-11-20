from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Equations.WidthDepthLink import (
    WidthDepthLink,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange import (
    Expression,
    Parameter,
    ParameterRole,
    frozen_mapping as FrozenMapping,
)


# the typed relation contributes one upstream identity and provenance beside the live depth scalar
def BindWidthDepth(
    Parameters: list[Parameter], WidthKey: str, DepthKey: str, Relation: WidthDepthLink
) -> tuple[Parameter, ...]:
    ParamIndexes = {ParamValue.id: Index for Index, ParamValue in enumerate(Parameters)}
    DepthIndex = ParamIndexes[DepthKey]
    DepthValue = Parameters[DepthIndex]
    WidthValue = Parameters[ParamIndexes[WidthKey]]
    RelationProvenance = TypedProvenance(
        Relation.RelationOwner, f"equation:{Relation.RelationOwner['object_index']}"
    )
    ProvenanceValue = DepthValue.provenance
    if ProvenanceValue is not None and RelationProvenance is not None:
        ProvenanceValue = ReplaceValue(
            ProvenanceValue, spans=(*ProvenanceValue.spans, *RelationProvenance.spans)
        )
    BoundValue = ReplaceValue(
        DepthValue,
        role=ParameterRole.KDerived,
        expression=Expression(Relation.RightText, (WidthValue.id,), "solidworks"),
        provenance=ProvenanceValue,
        attributes=FrozenMapping(
            {
                **DepthValue.attributes,
                "equation_source": Relation.SourceText,
                "equation_configuration_id": 0,
            }
        ),
    )
    return (*Parameters[:DepthIndex], BoundValue, *Parameters[DepthIndex + 1 :])
