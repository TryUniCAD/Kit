from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ReadColdMembers import ReadColdMembers
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument, ComponentDoc
from interchange.geometry.Models.SupportPlane import SupportPlane


# the neutral inverse retains each actual principal plane used by the generated component
def PlainPlanes(Planes: tuple[SupportPlane, ...]) -> tuple[SupportPlane, ...]:
    return tuple(
        ReplaceValue(Value, provenance=None, attributes=FreezeMapping()) for Value in Planes
    )


# the part inverse has to supply the full datum set referenced by the owning assembly
def PlanarLeaf(PartValue: ComponentDoc, Original: ComponentDoc) -> ComponentDoc:
    return ReplaceValue(
        PartValue,
        document=ReplaceValue(
            PartValue.document, support_planes=PlainPlanes(Original.document.support_planes)
        ),
    )


# clean intent is accepted only after the full regenerated assembly equals its strict source
def PlanarReadIn(Document: CadDocument) -> CadDocument:
    GraphValue = Document.assembly
    if GraphValue is None:
        raise ValueError("reopened planar assembly lacks its component graph")
    Definitions, ProjectedParts, Configs = ReadColdMembers(Document)
    OriginalParts = {Value.id: Value for Value in GraphValue.documents}
    RootId = GraphValue.root_definition_id
    RootName = next(Value.name for Value in Definitions if Value.id == RootId)
    Instances = tuple(
        ReplaceValue(
            Value, configuration_id=Configs[Value.definition_id].id,
            provenance=None, attributes=FreezeMapping(),
        )
        for Value in GraphValue.instances
    )
    return ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(Configs[RootId],),
        parameters=tuple(
            ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
            for Value in Document.parameters
        ),
        support_planes=PlainPlanes(Document.support_planes),
        feature_timeline=(),
        brep_payloads=(),
        diagnostics=(),
        capabilities=frozenset(),
        metadata=FreezeMapping({"name": RootName}),
        assembly=ReplaceValue(
            GraphValue,
            definitions=Definitions,
            documents=tuple(PlanarLeaf(Value, OriginalParts[Value.id]) for Value in ProjectedParts),
            instances=Instances,
            mate_entities=tuple(
                ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
                for Value in GraphValue.mate_entities
            ),
            mates=tuple(
                ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
                for Value in GraphValue.mates
            ),
            mate_groups=tuple(
                ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
                for Value in GraphValue.mate_groups
            ),
            attributes=FreezeMapping(),
        ),
    )
