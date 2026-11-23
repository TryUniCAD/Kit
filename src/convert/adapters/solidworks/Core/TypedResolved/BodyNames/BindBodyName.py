from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameProof import (
    BodyNameProof,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameSource import (
    BodyNameSource,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import (
    CheckBrepOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepTree import (
    CheckBrepTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.LinkLocalBody import (
    LinkLocalBody,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# native labels and local counts require complete binding to the selected neutral body
def BindBodyName(Document: CadDocument, GraphValue: BodyNameGraph) -> CadDocument:
    ModelValue = Document.brep
    if len(Document.bodies) != 1 or (
        ModelValue is None and GraphValue.LocalStoreKey is None
    ):
        raise ValueError("native body label requires one verified body owner")
    DesignBody = Document.bodies[0]
    ProofValue = BodyNameProof(GraphValue)
    Provenance = BodyNameSource(GraphValue)
    BodyAttrs = FreezeMapping(
        {**DesignBody.attributes, "solidworks.native_body": ProofValue}
    )
    MetadataValue = FreezeMapping(
        {**Document.metadata, "solidworks.native_body_names": ProofValue}
    )
    NamedBody = ReplaceValue(
        DesignBody, name=GraphValue.NameValue, provenance=Provenance, attributes=BodyAttrs
    )
    if ModelValue is None:
        return ReplaceValue(Document, bodies=(NamedBody,), metadata=MetadataValue)
    CheckBrepOwners(ModelValue, DesignBody.id)
    CheckBrepTree(ModelValue, GraphValue)
    KernelBody = ReplaceValue(
        ModelValue.bodies[0],
        design_body_id=DesignBody.id,
        provenance=Provenance,
        attributes=FreezeMapping(
            {**ModelValue.bodies[0].attributes, "solidworks.native_body": ProofValue}
        ),
    )
    BoundModel = ReplaceValue(ModelValue, bodies=(KernelBody,))
    if BoundModel.validate(frozenset((DesignBody.id,))) or any(
        BodyValue.design_body_id != DesignBody.id for BodyValue in BoundModel.bodies
    ):
        raise ValueError(
            "named native body did not bind completely to its neutral owner"
        )
    if GraphValue.LocalStoreKey is not None:
        _, TopologyValue = LinkLocalBody(BoundModel, DesignBody.id, DesignBody.topology)
        NamedBody = ReplaceValue(NamedBody, topology=TopologyValue)
    return ReplaceValue(
        Document,
        bodies=(NamedBody,),
        brep=BoundModel,
        metadata=MetadataValue,
    )
