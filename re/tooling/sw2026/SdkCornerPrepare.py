from __future__ import annotations

from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkBlindPartChecks import name, node, require
from SdkCornerChecks import corner
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive

CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def main():
    built = REQUEST["build"]
    blob = b64decode(built["blob"], validate=True)
    require(len(blob) == built["bytes"] and sha256(blob).hexdigest() == built["sha256"], "artifact custody differs")
    archive = SldprtArchive.from_bytes(blob)
    streams = {record.name: record.data for record in archive.records}
    require(len(streams) == 10 and streams.keys() == built["streams"].keys(), "actual native stream set differs")
    for stream, data in streams.items():
        row = built["streams"][stream]
        require(data == b64decode(row["data"], validate=True) and len(data) == row["bytes"] and sha256(data).hexdigest() == row["sha256"],
                "logical stream custody differs: " + stream)
    header = ReadHeaderGraph(streams["Contents/Config-0-ModelHeader"], 19000)
    config = ReadConfigMut(streams["Contents/Config-0"], 19000, header)
    manager = ReadCmgrMut(streams["Contents/CMgr"], 19000)
    context = MakeLinkContext(config, manager)
    resolved = ReadResolvedMut(streams["Contents/Config-0-ResolvedFeatures"], 19000, config.MapValue, context)
    model = node(config.RootValue, "moPart_c")
    features = resolved.RootsValue
    require(len(features) == built["feature_count"] == 19 and name(model) == built["name"], "model or resolved ownership differs")
    profile = node(features[-2], "moProfileFeature_c")
    origin, = [value for value in features if value.ClassValue.NameValue == "moOriginProfileFeature_c"]
    checked = corner(profile, origin, model, built["vertices_m"], True)
    require(node(features[-1], "moExtrusion_c").FieldsValue["f60"]["list"]["items"][0]["o"] is profile,
            "actual boss dependency lost its anchored profile")
    config_bytes, repeated = WriteConfigMut(model, 19000, header)
    resolved_bytes, repeated_resolved = WriteResolMut(features, resolved.ExtraFields, 19000, repeated.MapValue, context)
    comparisons = {"Contents/Config-0": config_bytes == streams["Contents/Config-0"],
                   "Contents/Config-0-ResolvedFeatures": resolved_bytes == streams["Contents/Config-0-ResolvedFeatures"]}
    require(all(comparisons.values()), "typed preparation changed native graph bytes")
    usage = {"config_load": config.ReportValue, "config_store": repeated.ReportValue,
             "resolved_load": resolved.ReportValue, "resolved_store": repeated_resolved.ReportValue}
    require(all(row["completed"] and not row["missing_schemas"] and not row["provisional_schemas"] for row in usage.values()),
            "anchor reached incomplete or provisional typed grammar")
    require(repeated.MapValue.CounterValue == built["config_map_counter"] and
            repeated_resolved.MapValue.CounterValue == built["resolved_map_counter"], "cross-stream map counters changed")
    imports = sorted(value for value, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/") and
                     value not in ("__main__", "SdkBlindPartChecks", "SdkCornerChecks"))
    require(not imports, "SDK preparation imported research implementation: " + repr(imports))
    return {"passed": True, "scope": "independent sdk typed preparation of a generated corner anchored rectangle",
            "artifact_sha256": sha256(blob).hexdigest(), "anchor": checked, "byte_identity": comparisons, "usage": usage,
            "config_map_counter": repeated.MapValue.CounterValue, "resolved_map_counter": repeated_resolved.MapValue.CounterValue,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imports),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
