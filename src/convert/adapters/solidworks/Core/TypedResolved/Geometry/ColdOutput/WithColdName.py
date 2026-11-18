from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.CheckColdBind import (
    CheckColdBind,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdNameProof import (
    ColdNameProof,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdNameSource import (
    ColdNameSource,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# only a fully proved cold output may replace the folder caption while all existing geometry and payload semantics remain intact
def WithColdName(
    Document: CadDocument, GeometryValue: PartGeometry | None
) -> CadDocument:
    if GeometryValue is None or GeometryValue.ColdValue is None:
        return Document
    OutputValue = GeometryValue.ColdValue
    CheckColdBind(Document, GeometryValue, OutputValue)
    ModelValue = GeometryValue.BrepValue
    ProofValue = ColdNameProof(OutputValue)
    BodyValue = Document.bodies[0]
    NamedBody = ReplaceValue(
        BodyValue,
        name=OutputValue.NameValue,
        provenance=ColdNameSource(OutputValue),
        attributes=FreezeMapping(
            {**BodyValue.attributes, "solidworks.authored_output_name": ProofValue}
        ),
    )
    KernelBody = ReplaceValue(
        ModelValue.bodies[0],
        attributes=FreezeMapping(
            {
                **ModelValue.bodies[0].attributes,
                "solidworks.authored_output_name": ProofValue,
            }
        ),
    )
    return ReplaceValue(
        Document,
        bodies=(NamedBody,),
        brep=ReplaceValue(ModelValue, bodies=(KernelBody,)),
        metadata=FreezeMapping(
            {**Document.metadata, "solidworks.cacheless_body_names": ProofValue}
        ),
    )
