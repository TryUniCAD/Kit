from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevRoot import (
    ReadRevRoot,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevSketch import (
    ReadRevSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# stripping source decoration is safe only behind the enclosing exact readback comparison
def ReadRevInput(DocumentValue: CadDocument, NameValue: str) -> CadDocument:
    if any(
        len(ItemsValue) != 1
        for ItemsValue in (
            DocumentValue.sketches,
            DocumentValue.parameters,
            DocumentValue.bodies,
            DocumentValue.configurations,
            DocumentValue.selections,
        )
    ):
        raise ValueError("SOLIDWORKS revolve readback requires one body profile and D1")
    (SketchValue,) = DocumentValue.sketches
    PlanesValue = tuple(Plane for Plane in DocumentValue.support_planes if Plane.id == SketchValue.support_plane_id)
    if len(PlanesValue) != 1:
        raise ValueError("SOLIDWORKS revolve readback requires one actual support datum")
    (PlaneValue,) = PlanesValue
    FeatureValue = ReadRevRoot(DocumentValue)
    return ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(DocumentValue.configurations[0], attributes=FreezeMapping()),),
        parameters=(ReplaceValue(DocumentValue.parameters[0], provenance=None, attributes=FreezeMapping()),),
        support_planes=(ReplaceValue(PlaneValue, provenance=None, attributes=FreezeMapping()),),
        sketches=(ReadRevSketch(SketchValue),),
        selections=(ReplaceValue(DocumentValue.selections[0], provenance=None, attributes=FreezeMapping()),),
        feature_timeline=(
            ReplaceValue(
                FeatureValue,
                order=0,
                input_feature_ids=(),
                provenance=None,
                attributes=FreezeMapping(),
            ),
        ),
        bodies=(
            ReplaceValue(
                DocumentValue.bodies[0],
                name=FeatureValue.name,
                topology=TopologyCounts(),
                provenance=None,
                attributes=FreezeMapping(),
            ),
        ),
        brep=None,
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
    )
