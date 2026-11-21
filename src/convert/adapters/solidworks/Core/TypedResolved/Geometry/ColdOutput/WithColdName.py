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
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# only a fully proved cold output may replace the folder caption while all existing geometry and payload semantics remain intact
def WithColdName(
    Document: CadDocument, GeometryValue: PartGeometry | None
) -> CadDocument:
    if GeometryValue is None:
        return Document
    OutputValue = GeometryValue.ColdValue
    if OutputValue is None:
        return UseProducerName(Document, GeometryValue)
    _ = CheckColdBind(Document, GeometryValue, OutputValue.BossValue)
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


# a derived cold label may follow only its actual typed producer and owned neutral solid
def UseProducerName(Document: CadDocument, GeometryValue: PartGeometry) -> CadDocument:
    BossValue = GeometryValue.ProducerValue
    if BossValue is None:
        return Document
    try:
        FeatureValue = CheckColdBind(Document, GeometryValue, BossValue)
        LabelValue = ReadNativeName(BossValue)
    except (ValueError, TypeError, KeyError):
        return Document
    if (
        FeatureValue.name != LabelValue
        or FeatureValue.provenance is None
        or not LabelValue.isascii()
        or not LabelValue.isprintable()
    ):
        return Document
    return ReplaceValue(
        Document,
        bodies=(
            ReplaceValue(
                Document.bodies[0], name=LabelValue, provenance=FeatureValue.provenance
            ),
        ),
    )
