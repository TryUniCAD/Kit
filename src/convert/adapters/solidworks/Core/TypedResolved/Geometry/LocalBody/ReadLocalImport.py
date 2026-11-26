from collections.abc import Sequence

from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyBrep import (
    ReadLocalBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalHead import (
    ReadLocalHead,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumDocument import Severity
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Records.RecordDiagnostic import Diagnostic


# an identified source solid is required geometry at the strict part boundary
def ReadLocalImport(
    Payloads: Sequence[BrepPayload],
    GroupData: bytes,
    OwnerValue: NativeFeature,
    *,
    Strict: bool,
) -> tuple[BrepModel | None, NativeFeature | None, Diagnostic | None]:
    if not any(
        Payload.source_stream == KLocalBodyStream
        and Payload.kind == "unknown"
        and Payload.data is not None
        and ReadLocalHead(Payload.data) is not None
        for Payload in Payloads
    ):
        return None, None, None
    try:
        return ReadLocalBrep(Payloads, GroupData, OwnerValue.name), OwnerValue, None
    except (KeyError, OverflowError, ValueError) as ErrorInfo:
        Message = f"SLDPRT local geometry rejected: {ErrorInfo}"
        if Strict:
            raise SldprtFormat(Message) from ErrorInfo
        return (
            None,
            None,
            Diagnostic(
                code="sldprt.local_geometry_rejected",
                message=Message,
                severity=Severity.WARNING,
                attributes=FreezeMapping(
                    {
                        "stream": KLocalBodyStream,
                        "native_object_id": OwnerValue.object_id,
                    }
                ),
            ),
        )
