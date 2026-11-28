from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevRoot import (
    ReadRevRoot,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevSketch import (
    ReadRevSketch,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadThinParam import (
    ReadThinParam,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# stripping source decoration is safe only behind the enclosing exact readback comparison
def ReadRevInput(
    DocumentValue: CadDocument, NameValue: str, *, IsThin: bool = False
) -> CadDocument:
    if any(
        len(ItemsValue) != 1
        for ItemsValue in (
            DocumentValue.sketches,
            DocumentValue.bodies,
            DocumentValue.configurations,
            DocumentValue.selections,
        )
    ) or len(DocumentValue.parameters) not in ((2, 3) if IsThin else (1,)):
        raise ValueError("SOLIDWORKS revolve readback requires one body profile and D1")
    (SketchValue,) = DocumentValue.sketches
    (PlaneValue,) = (
        Plane
        for Plane in DocumentValue.support_planes
        if Plane.id == SketchValue.support_plane_id
    )
    FeatureValue = ReadRevRoot(DocumentValue, IsThin=IsThin)
    return ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        configurations=(
            ReplaceValue(DocumentValue.configurations[0], attributes=FreezeMapping()),
        ),
        parameters=tuple(
            (
                ReadThinParam(Value)
                if IsThin
                else ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            )
            for Value in DocumentValue.parameters
        ),
        support_planes=(
            ReplaceValue(PlaneValue, provenance=None, attributes=FreezeMapping()),
        ),
        sketches=(ReadRevSketch(SketchValue, IsThin=IsThin),),
        selections=(
            ReplaceValue(
                DocumentValue.selections[0], provenance=None, attributes=FreezeMapping()
            ),
        ),
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
