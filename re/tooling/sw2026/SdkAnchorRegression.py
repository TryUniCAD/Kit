from __future__ import annotations

from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def main():
    blob = b64decode(REQUEST["blob"], validate=True)
    if sha256(blob).hexdigest() != REQUEST["sha256"]:
        raise ValueError("native regression input custody differs")
    archive = SldprtArchive.from_bytes(blob)
    streams = {record.name: record.data for record in archive.records}
    link = ReadNativeLink(archive, 0)
    config_bytes, config = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
    resolved_bytes, resolved = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                           19000, config.MapValue, link.ResolvedValue.ContextValue)
    comparisons = {"Contents/Config-0": config_bytes == streams["Contents/Config-0"],
                   "Contents/Config-0-ResolvedFeatures": resolved_bytes == streams["Contents/Config-0-ResolvedFeatures"]}
    if not all(comparisons.values()):
        raise ValueError("existing stream bytes changed")
    reports = (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue, config.ReportValue, resolved.ReportValue)
    if not all(row["completed"] and not row["missing_schemas"] and not row["provisional_schemas"] for row in reports):
        raise ValueError("native regression reached incomplete or provisional grammar")
    return {"passed": True, "input_sha256": sha256(blob).hexdigest(), "byte_identity": comparisons,
            "streams": {name: {"bytes": len(streams[name]), "sha256": sha256(streams[name]).hexdigest()} for name in comparisons},
            "config_map_counter": config.MapValue.CounterValue, "resolved_map_counter": resolved.MapValue.CounterValue,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
