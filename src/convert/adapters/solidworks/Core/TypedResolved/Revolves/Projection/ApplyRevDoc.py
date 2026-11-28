from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevDoc import (
    BindRevDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.ReportRevolve import (
    ReportRevolve,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# the public model must replace all linked revolve semantics together while preserving unrelated source records
def ApplyRevDoc(
    DocumentValue: CadDocument, LinkValue: NativeLink, OwnerValue: RevolveOwner
) -> CadDocument:
    BoundValue = BindRevDoc(DocumentValue, LinkValue, OwnerValue)
    return ReplaceValue(
        BoundValue,
        metadata=FreezeMapping(
            {
                **DocumentValue.metadata,
                "solidworks.typed_revolve_semantics": {
                    "status": "projected",
                    "revolutions": (ReportRevolve(LinkValue, OwnerValue),),
                    "typed_geometry_projection": True,
                    "full_document_qualified": False,
                    "public_writer_qualified": False,
                },
            }
        ),
    )
