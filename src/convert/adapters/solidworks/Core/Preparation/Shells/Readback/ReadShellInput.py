from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import (
    ReadColdSketch,
)
from convert.adapters.solidworks.Core.Preparation.Shells.Readback.ReadShellHist import (
    CheckShellRead,
    ReadShellHist,
)
from convert.adapters.solidworks.Core.Preparation.Shells.Readback.ReadShellWall import (
    ReadShellWall,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordTopology import TopologyCounts


# construction uses just the actual input owners while the unchanged complete source remains available for validation
def ReadShellInput(DocumentValue: CadDocument, NameValue: str) -> CadDocument:
    CheckShellRead(DocumentValue)
    DocumentValue.assert_valid()
    (ConfigValue,) = DocumentValue.configurations
    (SketchValue,) = DocumentValue.sketches
    (BodyValue,) = DocumentValue.bodies
    (CapValue,) = DocumentValue.selections
    StockStep, ShellStep = ReadShellHist(DocumentValue, SketchValue.id)
    (DepthId,) = StockStep.parameter_ids
    (WallId,) = ShellStep.parameter_ids
    Drivers = {Value.id: Value for Value in DocumentValue.parameters}
    if set(Drivers) != {DepthId, WallId} or DepthId == WallId:
        raise ValueError("SOLIDWORKS shell compilation needs two independent drivers")
    BossValue, Depth = ReadColdBoss(StockStep, Drivers[DepthId])
    Shell, WallValue = ReadShellWall(ShellStep, Drivers[WallId])
    (PlaneValue,) = (
        Value
        for Value in DocumentValue.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    return ReplaceValue(
        DocumentValue,
        source=ReplaceValue(DocumentValue.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(ConfigValue, attributes=FreezeMapping()),),
        parameters=(Depth, WallValue),
        support_planes=(
            ReplaceValue(PlaneValue, provenance=None, attributes=FreezeMapping()),
        ),
        sketches=(ReadColdSketch(SketchValue),),
        selections=(ReplaceValue(CapValue, provenance=None),),
        feature_timeline=(BossValue, Shell),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=Shell.name,
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
