from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Circle.IsCirclePart import (
    IsCirclePart,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdDisc import (
    ReadColdDisc,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdOwners import (
    ReadColdOwners,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import (
    ReadColdSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordParameter import Parameter
from interchange.Records.RecordTopology import TopologyCounts


# only the shared plain inputs reach construction while the enclosing writer verifies all readback state
def ColdReadInput(Document: CadDocument, NameValue: str) -> CadDocument:
    IsCircle = IsCirclePart(Document)
    if (
        Document.assembly is not None
        or Document.brep_payloads
        or Document.meshes
        or Document.materials
        or len(Document.parameters) != (2 if IsCircle else 1)
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
    Depths = tuple(
        ItemValue
        for ItemValue in Document.parameters
        if not IsCircle or ItemValue.id not in Sketch.parameter_ids
    )
    if len(Depths) != 1:
        raise ValueError("SOLIDWORKS cold readback lacks its unique boss depth")
    (Driver,) = Depths
    Owner, Plane = ReadColdOwners(Document, Sketch, Driver)
    Feature, Depth = ReadColdBoss(Owner, Driver)
    Parameters: tuple[Parameter, ...] = (Depth,)
    if IsCircle:
        (Radial,) = (Value for Value in Document.parameters if Value.id != Driver.id)
        Sketch, Radial = ReadColdDisc(Sketch, Radial, Owner.input_feature_ids[0])
        Parameters = (Depth, Radial)
    else:
        Sketch = ReadColdSketch(Sketch)
    return ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(Config, attributes=FreezeMapping()),),
        parameters=Parameters,
        support_planes=(
            ReplaceValue(Plane, attributes=FreezeMapping(), provenance=None),
        ),
        sketches=(Sketch,),
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
