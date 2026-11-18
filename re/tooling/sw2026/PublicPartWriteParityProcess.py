from __future__ import annotations

from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]).resolve(strict=True)
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "re/tooling/sw2026")]

from AuthorSdkCircleRequests import make_document
from convert import open_document, write_document
from interchange.document.Behavior import DocumentIo
from interchange.document.Models.DocumentProvenance import HasProvenance
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.Features.FeatureExtrude import ExtrudeEnd
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


def document_value(role):
    if role == "polygon":
        return MakePlainDoc("RegistrationPolygon", 32.7, 17.9, 8.1)
    if role == "diameter-front":
        return make_document("RegistrationDiameterFront", "Front Plane", (2.13, -3.97), 9.27, 13.17,
                             "diameter", ExtrudeEnd.KBlind, False, None)
    if role == "radius-top-reverse":
        return make_document("RegistrationRadiusTop", "Top Plane", (-4.31, 6.79), 7.83, 11.29,
                             "radius", ExtrudeEnd.KBlind, True, None)
    raise ValueError("unknown qualified standalone profile")


def run(role):
    document = document_value(role)
    emitter = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
    emitter.ReadTime = lambda: 1794001000
    codecs = tuple(lookup(name) for name in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1"))
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    target = BytesIO()
    audit.BeginBuild()
    result = write_document(document, target, destination_format="solidworks.sldprt", allow_carrier=False,
                            values={"final_destination": "C:\\KitRegistryPartProof\\" + document.metadata["name"] + ".SLDPRT",
                                    "require_native_transfers": True})
    payload = target.getvalue()
    decoded = open_document(payload, source_format="solidworks.sldprt", include_brep=False, include_tessellation=False)
    decoded.assert_valid()
    if audit.DeniedReads or not result.vendor_loadable or not result.application_usable or len(result.native_capabilities) != 6:
        raise ValueError("standalone part behavior or runtime independence changed")
    return {"passed": True, "role": role, "worker_pid": os.getpid(), "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
            "document_json": decoded.to_json(indent=None), "native_capabilities": len(result.native_capabilities),
            "runtime_input_file_reads": 0, "native_processes_started": 0}


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[2]), sort_keys=True))
