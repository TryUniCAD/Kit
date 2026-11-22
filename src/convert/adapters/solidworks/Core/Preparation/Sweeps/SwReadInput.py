from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Format import KPartFormatId
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# any native sweep readback must pass the additional canonical regeneration check
def IsSwReadback(DocumentValue: CadDocument) -> bool:
    return DocumentValue.source.format_id.casefold() == KPartFormatId


# the constructor receives modeled inputs while a second comparison protects every derived field
def SwReadInput(DocumentValue: CadDocument) -> CadDocument:
    return ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        parameters=tuple(
            ReplaceValue(Value, attributes=FreezeMapping(), provenance=None)
            for Value in DocumentValue.parameters
        ),
        support_planes=tuple(
            ReplaceValue(Value, provenance=None)
            for Value in DocumentValue.support_planes
        ),
        sketches=tuple(
            ReplaceValue(Value, attributes=FreezeMapping(), provenance=None)
            for Value in DocumentValue.sketches
        ),
        feature_timeline=tuple(
            ReplaceValue(Value, provenance=None)
            for Value in DocumentValue.feature_timeline
        ),
        bodies=tuple(
            ReplaceValue(
                Value,
                topology=TopologyCounts(),
                attributes=FreezeMapping(),
                provenance=None,
            )
            for Value in DocumentValue.bodies
        ),
        brep=None,
        capabilities=frozenset(),
    )
