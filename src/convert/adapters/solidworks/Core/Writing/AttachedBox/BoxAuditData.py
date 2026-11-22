from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import (
    AttachedBoxPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxSourceCaps import (
    KBoxEvidenceCaps,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentProvenance import IterProvenance
from interchange.Payloads.PayloadRecord import BrepPayload


# exact source associations survive json through digests and explicit independent owners
def BoxAuditData(
    PlanValue: AttachedBoxPlan,
    SourcePair: tuple[BrepPayload, BrepPayload],
    Shapes: tuple[dict[str, object], ...],
) -> Mapping[str, object]:
    Document = PlanValue.SourceDocument
    BoxValue = PlanValue.PartSource
    BodyValue, Feature = Document.bodies[0], Document.feature_timeline[0]
    Objects = NativeRows(NativeRecord(Document.metadata["freecad"])["objects"])
    return FreezeMapping(
        {
            "source_sha256": Document.source.sha256,
            "source_native_byte_replay": False,
            "application_version": Document.source.application_version,
            "evidence_only_capabilities": sorted(
                Value.value for Value in KBoxEvidenceCaps
            ),
            "archive_and_binding": [
                {"id": Value.id, "sha256": Value.sha256} for Value in SourcePair
            ],
            "shape_caches": list(Shapes),
            "source_object_order": [
                {
                    "id": Value["object_id"],
                    "name": Value["name"],
                    "type": Value["type_id"],
                    "dependencies": list(
                        CastValue(Sequence[str], Value["dependencies"])
                    ),
                }
                for Value in Objects
            ],
            "source_provenance": [
                {
                    "adapter": Value.adapter,
                    "id": Value.native_id,
                    "spans": [
                        {
                            "stream": SpanValue.stream,
                            "offset": SpanValue.offset,
                            "length": SpanValue.length,
                            "kind": SpanValue.record_kind,
                        }
                        for SpanValue in Value.spans
                    ],
                }
                for Value in IterProvenance(Document)
            ],
            "native_geometry": {
                "body": {
                    "source_id": BodyValue.id,
                    "target_name": BoxValue.SourceBodyName,
                },
                "feature": {
                    "source_id": Feature.id,
                    "target_name": BoxValue.SourceFeatureName,
                },
                "drivers": dict(BoxValue.ParameterBindings),
                "planes": [
                    {"source_id": Value.id, "source_name": Value.name}
                    for Value in Document.support_planes
                ],
                "axes": [
                    {
                        "source_id": Value.RecordId,
                        "role": Value.RoleName,
                        "target_name": Value.LabelValue,
                    }
                    for Value in PlanValue.OriginAxes.AxisValues
                ],
            },
        }
    )
