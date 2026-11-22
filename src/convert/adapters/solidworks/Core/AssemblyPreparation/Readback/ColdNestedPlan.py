from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.NestedAssemblyPlan import (
    NestedAsmPlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import (
    ReadNestedAsm,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.CheckColdAsm import (
    CheckColdAsm,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ReadColdMembers import (
    ReadColdMembers,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ReadExactPlace import (
    ReadExactPlace,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# the provisional clean input is safe only after the real writer verifies the entire independent readback
def ColdNestedPlan(Document: CadDocument) -> NestedAsmPlan:
    CheckColdAsm(Document)
    Document.assert_valid()
    GraphValue = Document.assembly
    if GraphValue is None:
        raise ValueError(
            "reopened nested source requires a complete owned definition graph"
        )
    Definitions, Parts, Configs = ReadColdMembers(Document)
    Placements = {Value.id: ReadExactPlace(Value) for Value in GraphValue.instances}
    Instances = tuple(
        ReplaceValue(
            Value,
            configuration_id=Configs[Value.definition_id].id,
            attributes=FreezeMapping(),
            provenance=None,
        )
        for Value in GraphValue.instances
    )
    RootId = GraphValue.root_definition_id
    RootName = next(Value.name for Value in Definitions if Value.id == RootId)
    Projected = ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(Configs[RootId],),
        feature_timeline=(),
        brep_payloads=(),
        support_planes=tuple(
            ReplaceValue(Value, attributes=FreezeMapping(), provenance=None)
            for Value in Document.support_planes
        ),
        diagnostics=(),
        capabilities=frozenset(),
        metadata=FreezeMapping({"name": RootName}),
        assembly=ReplaceValue(
            GraphValue,
            definitions=Definitions,
            documents=Parts,
            instances=Instances,
            attributes=FreezeMapping(),
        ),
    )
    return ReadNestedAsm(Projected, ExactPlacements=Placements)
