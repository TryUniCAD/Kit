from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Equations.HasEqIntent import (
    HasEqIntent,
)
from convert.adapters.solidworks.Core.Preparation.Equations.ReadEqDrivers import (
    ReadEqDrivers,
)
from convert.adapters.solidworks.Core.Preparation.Equations.ReadEqSketch import (
    ReadEqSketch,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import (
    ReadColdSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# exact readback verification needs a construction copy of the owned neutral inputs
def ColdReadInput(Document: CadDocument, NameValue: str) -> CadDocument:
    IsEquation = HasEqIntent(Document)
    if (
        Document.assembly is not None
        or len(Document.parameters) != (3 if IsEquation else 1)
        or Document.brep_payloads
        or Document.meshes
        or Document.materials
        or any(
            len(RowsValue) != 1
            for RowsValue in (
                Document.configurations,
                Document.sketches,
                Document.bodies,
            )
        )
    ):
        raise ValueError(
            "SOLIDWORKS cold readback requires one ordinary body profile and D1"
        )
    Sketch, BodyValue, Config = (
        Document.sketches[0],
        Document.bodies[0],
        Document.configurations[0],
    )
    Driver, SketchDrivers = (
        ReadEqDrivers(Sketch, Document.parameters)
        if IsEquation
        else (Document.parameters[0], ())
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
        parameters=(*SketchDrivers, Parameter),
        support_planes=(
            ReplaceValue(Planes[0], attributes=FreezeMapping(), provenance=None),
        ),
        sketches=((ReadEqSketch if IsEquation else ReadColdSketch)(Sketch),),
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
