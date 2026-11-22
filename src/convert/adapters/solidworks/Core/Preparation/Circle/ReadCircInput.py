from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Circle.ReadCircBoss import (
    ReadCircBoss,
)
from convert.adapters.solidworks.Core.Preparation.Circle.ReadCircDrive import (
    ReadCircDrive,
)
from convert.adapters.solidworks.Core.Preparation.Circle.ReadCircSketch import (
    ReadCircSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# construction extracts actual editable owners while publication still compares the complete untouched source
def ReadCircInput(Document: CadDocument, NameValue: str) -> CadDocument:
    Document.assert_valid()
    (SketchValue,) = Document.sketches
    (BodyValue,) = Document.bodies
    (Config,) = Document.configurations
    (PlaneValue,) = (
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    (BossValue,) = (
        Value
        for Value in Document.feature_timeline
        if Value.id == BodyValue.final_feature_id
    )
    (Profile,) = (
        Value
        for Value in Document.feature_timeline
        if Value.id in BossValue.input_feature_ids
    )
    if (
        BossValue.sketch_id != SketchValue.id
        or Profile.sketch_id != SketchValue.id
        or Profile.parameter_ids != SketchValue.parameter_ids
    ):
        raise ValueError(
            "SOLIDWORKS circle readback requires its actual sketch and boss lineage"
        )
    (RadialId,) = Profile.parameter_ids
    Drivers = {Value.id: Value for Value in Document.parameters}
    if len(Drivers) != 1 + len(BossValue.parameter_ids) or set(Drivers) != {
        RadialId,
        *BossValue.parameter_ids,
    }:
        raise ValueError(
            "SOLIDWORKS circle readback requires distinct radial and end drivers"
        )
    Radial = ReadCircDrive(Drivers[RadialId], Profile.id, "D1", Radial=True)
    BossStep, Depths = ReadCircBoss(
        BossValue, tuple(Drivers[Value] for Value in BossValue.parameter_ids)
    )
    return ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(Config, attributes=FreezeMapping()),),
        parameters=(ReplaceValue(Radial, owner_id=SketchValue.id), *Depths),
        support_planes=(
            ReplaceValue(PlaneValue, attributes=FreezeMapping(), provenance=None),
        ),
        sketches=(ReadCircSketch(SketchValue, Radial),),
        feature_timeline=(BossStep,),
        selections=(),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=BossStep.name,
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
