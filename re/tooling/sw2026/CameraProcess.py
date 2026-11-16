from __future__ import annotations

import base64
import codecs
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from RoundTrip import PLANS, stream_roundtrip
from StringCorpus import GraphProof, LoadModels
from builders.Camera import construct_camera_part
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt

REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.loads(sys.stdin.read())
AUDIT.BeginBuild()
CONSTRUCTION = construct_camera_part(registry=REGISTRY, **REQUEST)
BLOB = build_sldprt(CONSTRUCTION.streams)
ARCHIVE = SldprtArchive.from_bytes(BLOB)
COMPARISONS = {name: stream_roundtrip(ARCHIVE, name, REGISTRY, {**PLANS, **REGISTRY.plans}, True) for name in CONSTRUCTION.streams if name != "swXmlContents/KeyWords"}
MODELS = LoadModels(ARCHIVE, REGISTRY)
DOCUMENT = MODELS["Contents/Definition"]["document"].head
RESOLVED = "Contents/Config-0-ResolvedFeatures"
GRAPH = GraphProof(MODELS[RESOLVED]["document"], MODELS[RESOLVED]["reader"], RESOLVED, MODELS["Contents/Config-0"])
RESULT = {
    "schema": "kit.sw2026.fresh-camera-part.v1",
    "blob": base64.b64encode(BLOB).decode("ascii"),
    "streams": COMPARISONS,
    "sizes": {name: len(raw) for name, raw in CONSTRUCTION.streams.items()},
    "view_fields": {"orientation": DOCUMENT["fae8"], "pan_zoom": DOCUMENT["faf0"]},
    "graph": GRAPH,
    "features": [node.cls for node in CONSTRUCTION.features],
    "points": CONSTRUCTION.profile.point_count,
    "arcs": CONSTRUCTION.profile.arc_count,
    "lines": CONSTRUCTION.profile.line_count,
    "next_id": CONSTRUCTION.next_id,
    "map_count": CONSTRUCTION.configuration_map_count,
    "module_reads": AUDIT.ModuleReads,
    "denied_reads": AUDIT.DeniedReads,
    "vendor_acceptance": "unverified",
    "heldout_native_payloads_read": False,
    "native_acceptance": False,
}
print(json.dumps(RESULT, allow_nan=False))
