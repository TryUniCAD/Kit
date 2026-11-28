from collections.abc import Callable
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import (
    ReadColdSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch as CadSketch
from interchange.Records.RecordTopology import TopologyCounts


# only the shared plain inputs reach construction while the enclosing writer verifies all readback state
def ColdReadInput(
    Document: CadDocument,
    NameValue: str,
    *,
    SketchReader: Callable[[CadSketch], CadSketch] = ReadColdSketch,
) -> CadDocument:
    if (
        Document.assembly is not None
        or Document.brep_payloads
        or Document.meshes
        or Document.materials
        or any(
            len(RowsValue) != 1
            for RowsValue in (
                Document.configurations,
                Document.parameters,
                Document.sketches,
                Document.bodies,
            )
        )
    ):
        raise ValueError(
            "SOLIDWORKS cold readback requires one ordinary body profile and D1"
        )
    Sketch, Driver, BodyValue, Config = (
        Document.sketches[0],
        Document.parameters[0],
        Document.bodies[0],
        Document.configurations[0],
    )
    Owners = tuple(
        ItemValue
        for ItemValue in Document.feature_timeline
        if ItemValue.id == Driver.owner_id
    )
    Planes = tuple(
        ItemValue
        for ItemValue in Document.support_planes
        if ItemValue.id == Sketch.support_plane_id
    )
    if len(Owners) != 1 or len(Planes) != 1 or Owners[0].sketch_id != Sketch.id:
        raise ValueError(
            "SOLIDWORKS cold readback lacks an exact feature and datum owner"
        )
    Owner = Owners[0]
    SketchLinks = tuple(
        ItemValue.id
        for ItemValue in Document.feature_timeline
        if ItemValue.id in Owner.input_feature_ids and ItemValue.sketch_id == Sketch.id
    )
    if len(SketchLinks) != 1 or Owner.input_feature_ids != SketchLinks:
        raise ValueError("SOLIDWORKS cold boss requires its owned sketch dependency")
    Feature, Parameter = ReadColdBoss(Owner, Driver)
    return ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(Config, attributes=FreezeMapping()),),
        parameters=(Parameter,),
        support_planes=(
            ReplaceValue(Planes[0], attributes=FreezeMapping(), provenance=None),
        ),
        sketches=(SketchReader(Sketch),),
        selections=(),
        feature_timeline=(Feature,),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=Feature.name,
                topology=TopologyCounts(),
                attributes=FreezeMapping(),
                provenance=None,
            ),
        ),
        brep=None,
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
    )
