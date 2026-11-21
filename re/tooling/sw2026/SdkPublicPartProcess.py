from __future__ import annotations

from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import sys


ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from convert import open_document, write_document
from interchange.document.Behavior import DocumentIo
from interchange.document.Models.DocumentProvenance import HasProvenance
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData


EMITTER = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
CODECS = tuple(lookup(value) for value in ("utf-8", "utf-16-le", "latin-1"))
INPUT = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    request = INPUT["request"]
    document = FromData(request["document"])
    EMITTER.ReadTime = lambda: request["written_at"]
    buffer = BytesIO()
    result = write_document(
        document, buffer, destination_format="solidworks.sldprt", allow_carrier=False,
        values={"final_destination": request["destination"], "require_native_transfers": True},
    )
    blob = buffer.getvalue()
    artifact_sha = sha256(blob).hexdigest()
    require(artifact_sha == INPUT["candidate_sha256"], "public output differs from the exact native oracle input")
    require(result.bytes_written == len(blob) and result.path is None and len(result.native_capabilities) == 6
            and result.vendor_loadable and result.application_usable, "public result lost its qualified native transfer evidence")
    readback = open_document(blob, source_format="solidworks.sldprt", include_brep=False, include_tessellation=False)
    sketch, = readback.sketches
    want = document.sketches[0]
    require(len(readback.feature_timeline) == 19 and len(sketch.entities) == len(want.entities)
            and len(sketch.closed_profile_entity_ids) == 1, "strict public read did not restore the exact ordinary sketch")
    pairs = zip(sketch.entities, want.entities, strict=True)
    require(all(a.kind == b.kind == "line"
                and all(abs(left - right) < 1e-10 for left, right in zip(
                    (a.geometry.start.x, a.geometry.start.y, a.geometry.end.x, a.geometry.end.y),
                    (b.geometry.start.x, b.geometry.start.y, b.geometry.end.x, b.geometry.end.y), strict=True))
                for a, b in pairs), "public read changed the actual ordered line endpoints")
    require(not AUDIT.DeniedReads, "public runtime tried to read input data")
    return {"passed": True, "bytes": len(blob), "candidate_sha256": artifact_sha,
            "native_capabilities": len(result.native_capabilities), "logical_shape_lines": len(sketch.entities),
            "runtime_input_file_reads": len(AUDIT.DeniedReads)}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
