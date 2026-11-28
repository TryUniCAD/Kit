from dataclasses import replace as ReplaceValue

from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordTopology import TopologyCounts


# derived sketch support and seam evidence remains subject to the complete regenerated comparison
def SwInputSketch(SketchValue: Sketch) -> Sketch:
    return ReplaceValue(
        SketchValue,
        attributes=FreezeMapping(),
        provenance=None,
        entities=tuple(
            ReplaceValue(EntityValue, attributes=FreezeMapping())
            for EntityValue in SketchValue.entities
        ),
    )


# explicit cad inputs are taken from the neutral model before comparing the full source snapshot
def SwReadInput(DocumentValue: CadDocument) -> CadDocument:
    return ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        configurations=tuple(
            ReplaceValue(Value, attributes=FreezeMapping())
            for Value in DocumentValue.configurations
        ),
        parameters=tuple(
            ReplaceValue(Value, attributes=FreezeMapping(), provenance=None)
            for Value in DocumentValue.parameters
        ),
        support_planes=tuple(
            ReplaceValue(Value, provenance=None)
            for Value in DocumentValue.support_planes
        ),
        sketches=tuple(SwInputSketch(Value) for Value in DocumentValue.sketches),
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
