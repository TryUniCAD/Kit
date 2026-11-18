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
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# authored labels can be projected only after the complete brep has a valid neutral body owner
def BindBodyName(Document: CadDocument, GraphValue: BodyNameGraph) -> CadDocument:
    ModelValue = Document.brep
    if ModelValue is None or len(Document.bodies) != 1:
        raise ValueError("native body label requires complete public geometry")
    DesignBody = Document.bodies[0]
    CheckBrepOwners(ModelValue, DesignBody.id)
    CheckBrepTree(ModelValue, GraphValue)
    ProofValue = BodyNameProof(GraphValue)
    Provenance = BodyNameSource(GraphValue)
    BodyAttrs = FreezeMapping(
        {**DesignBody.attributes, "solidworks.native_body": ProofValue}
    )
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
    NamedBody = ReplaceValue(
        DesignBody,
        name=GraphValue.NameValue,
        provenance=Provenance,
        attributes=BodyAttrs,
    )
    return ReplaceValue(
        Document,
        bodies=(NamedBody,),
        brep=BoundModel,
        metadata=FreezeMapping(
            {**Document.metadata, "solidworks.native_body_names": ProofValue}
        ),
    )
