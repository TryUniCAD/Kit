from __future__ import annotations

from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026/serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from defs.ConfigPart import load_config
from defs.ResolvedCore import document_context
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive

REGISTRY = registry()
CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def main():
    blob = b64decode(REQUEST["blob"], validate=True)
    if sha256(blob).hexdigest() != REQUEST["sha256"]:
        raise ValueError("native seeded regression custody differs")
    archive = SldprtArchive.from_bytes(blob)
    _, prior = load_config(archive.require("Contents/Config-0"), REGISTRY, 19000, archive=archive, name="Contents/Config-0")
    seed = prior._maps.Snapshot()
    stream = "Contents/Config-0-ResolvedFeatures"
    context = document_context(archive, stream, REGISTRY, 19000)
    decoded = ReadResolvedMut(archive.require(stream), 19000, seed, context)
    encoded, repeated = WriteResolMut(decoded.RootsValue, decoded.ExtraFields, 19000, seed, context)
    if encoded != archive.require(stream):
        raise ValueError("disclosed native anchored resolved bytes changed")
    reports = (decoded.ReportValue, repeated.ReportValue)
    if not all(row["completed"] and not row["missing_schemas"] and not row["provisional_schemas"] for row in reports):
        raise ValueError("native anchor resolved profile reached incomplete grammar")
    classes = ("moCompSketchEntHandle_c", "moPointBackedUpData_c", "moSketchExtRef_w", "sgExtEnt_c", "sk.sgLogG2Dim.FUN_4c58b970")
    if not all(row["schema_calls"].get(name) == 1 for row in reports for name in classes):
        raise ValueError("native regression did not exercise all four concrete owners and its coincidence record")
    return {"passed": True, "scope": "sdk resolved codec only, explicitly seeded by research parsed native configuration map",
            "input_sha256": sha256(blob).hexdigest(), "stream": stream, "stream_bytes": len(encoded),
            "stream_sha256": sha256(encoded).hexdigest(), "byte_identity": True,
            "schema_calls": {name: decoded.ReportValue["schema_calls"][name] for name in classes},
            "config_seed_counter": seed.CounterValue, "resolved_map_counter": repeated.MapValue.CounterValue,
            "config_sdk_qualified": False, "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
