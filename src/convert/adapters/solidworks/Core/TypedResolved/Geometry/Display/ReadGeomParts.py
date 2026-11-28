from interchange import BrepPayload, Diagnostic, Severity
from interchange import frozen_mapping as FrozenMapping
from interchange.brep.Topology.BrepModel import BrepModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Display.ReadGeomMessage import (
    ReadGeomMessage,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)


# reconstructed geometry and its exact provenance diagnostic must enter the existing part reader together without inventing a cached payload
def ReadGeomParts(
    GeometryValue: PartGeometry,
) -> tuple[tuple[BrepPayload, ...], tuple[Diagnostic, ...], BrepModel]:
    MethodValue = str(GeometryValue.EvidenceValue.get("method", ""))
    Diagnostics = (
        Diagnostic(
            code="sldprt.brep_reconstructed",
            message=ReadGeomMessage(MethodValue),
            severity=Severity.INFO,
            attributes=FrozenMapping(GeometryValue.EvidenceValue),
        ),
    )
    return (), Diagnostics, GeometryValue.BrepValue
