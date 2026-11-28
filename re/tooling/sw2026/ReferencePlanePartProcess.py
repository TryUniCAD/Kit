from __future__ import annotations

from base64 import b64encode
import codecs
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Core import DOCUMENT_VERSION_2026
from RoundTrip import PLANS, stream_roundtrip
from builders.Part import construct_part
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved, store_resolved_state
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt


SOURCE_LOCK_SHA256 = "c61560deff9c84addd65db48664ce6a5488ad3eecde9a070c62a215a5541d703"
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))


def require(value, message):
    if not value:
        raise ValueError(message)


def point(value):
    return tuple(value[axis] for axis in "xyz")


def inspect_plane(archive, rules, request):
    config_name = "Contents/Config-0"
    resolved_name = config_name + "-ResolvedFeatures"
    config, initial = load_config(archive.require(config_name), rules, DOCUMENT_VERSION_2026, archive=archive, name=config_name)
    resolved, final = load_resolved(archive.require(resolved_name), rules, DOCUMENT_VERSION_2026,
                                   archive=archive, name=resolved_name, seed=initial.map_state())
    require(not config.tail and not resolved.tail, "the generated plane graph has an unread tail")
    config_bytes, state = store_config_state(config, rules, DOCUMENT_VERSION_2026)
    resolved_bytes, emitted = store_resolved_state(resolved, rules, DOCUMENT_VERSION_2026, seed=state)
    require(config_bytes == archive.require(config_name) and resolved_bytes == archive.require(resolved_name)
            and initial.count == state.count == final.base and final.count == emitted.count,
            "the generated plane graph lost its exact linked archive map")
    model, = config.roots
    values = request["document"]
    plane_name = request["offset_plane_discovery"]["name"]
    named = {node["f18"]["f08"]: node for node in resolved.roots}
    plane = named[plane_name]
    profile = named[values["sketch_name"]]
    data = plane["f6f8"]
    selected = data["f90"]["f58"]
    support = named[request["presentation"]["plane_names"][values["plane_axis"]]]
    display = data["f98"]
    handle, = (row["o"] for row in display["f850"])
    dimension = handle["ff0"]
    parameter = dimension["f28"]
    require((data.cls, display.cls, handle.cls, dimension.cls, parameter.cls) ==
            ("moFaceRefPlnData_c", "moDisplayDistanceDim_c", "moFeatureDimHandle_c",
             "ParallelPlaneDistanceDim_c", "moLengthParameter_c"), "the generated plane lost its concrete value graph")
    require(selected["f58"]["owner"] is model and selected["ff0"]["f00"] == support["f08"]
            and selected["f100"] == "xyz".index(values["plane_axis"]) + 1,
            "the generated plane lost its actual local principal support")
    require(profile["pd_f78"]["f58"]["owner"] is model and profile["pd_f78"]["ff0"]["f00"] == plane["f08"]
            and profile["pd_f78"]["f100"] == 0,
            "the generated sketch lost its authored offset-plane support")
    require(parameter["f58"] == request["offset_plane_discovery"]["distance_m"]
            and parameter["f18"]["f08"] == "D1" and parameter["f08"] == -1
            and dimension["f50"] + 1 == plane["f08"],
            "the plane dimension must consume its own ID before plane publication")
    require(data["fa0"] == int(request["offset_plane_discovery"]["reverse"])
            and data["f5c"] == 5 and data["fa4"] == 1 and data["fb4"] == 0 and not data["has_fa8"],
            "the compatibility plane lost its independently constructed options")
    require(data["f54"] == data["f58"] == -4 and all(data[f"b{index}"] == 0.0 for index in range(4))
            and plane["f6dc"] == 4 and dimension["has_fe0"] == dimension["has_ff0"] == 0,
            "the first offset candidate must retain its explicit constructor cache lifecycle")
    return {
        "plane_name": plane_name, "plane_feature_id": plane["f08"], "support_feature_id": support["f08"],
        "profile_feature_id": profile["f08"], "value_dimension_id": dimension["f50"],
        "parameter_name": parameter["f18"]["f08"], "distance_m": parameter["f58"], "reverse": bool(data["fa0"]),
        "root_m": point(data["root"]), "normal": point(data["normal"]), "world_to_plane": data["f20"],
        "sketch_world_to_local": profile["pd_ff0"], "plane_kind": 0,
        "constructor_mode_words": {key: data[key] for key in ("f50", "f54", "f58", "f5c", "f60", "f64", "fa0", "fa4", "fb4")},
        "border": tuple(data[f"b{index}"] for index in range(4)),
        "linked_map_round_trips": 2, "map_base": initial.base, "config_map_count": initial.count,
        "resolved_map_base": final.base, "resolved_map_count": final.count,
    }


def build_report(request):
    require(isinstance(request, dict) and "offset_plane_discovery" in request,
            "the offset process requires an explicit independently authored offset-plane request")
    rules = registry()
    AUDIT.BeginBuild()
    part = construct_part(registry=rules, **request)
    payload = build_sldprt(part.streams)
    archive = SldprtArchive.from_bytes(payload)
    require(archive.streams == part.streams, "the physical container changed the generated stream set")
    inspected = inspect_plane(archive, rules, request)
    reports = {name: stream_roundtrip(archive, name, rules, {**PLANS, **rules.plans}, linked=True)
               for name in part.streams if name != "swXmlContents/KeyWords"}
    require(all(row["passed"] for row in reports.values()), "a generated stream failed exact round-trip")
    return {
        "schema": "kit.sw2026.generated-offset-plane-discovery.v1", "native_acceptance": False,
        "vendor_loadable": False, "application_usable": False, "heldout_inputs_tested": 0,
        "pre_writer_source_lock_sha256": SOURCE_LOCK_SHA256, "writer_output_count": 1,
        "constructor_cache_load_neutrality_qualified": False,
        "inspection": inspected, "streams": {name: {key: row.get(key) for key in ("passed", "bytes", "sha256", "tail", "error")}
                                             for name, row in reports.items()},
        "native": {"sha256": sha256(payload).hexdigest(), "bytes": len(payload),
                   "artifact_base64": b64encode(payload).decode("ascii")},
        "features": [{"class": node.cls, "id": node["f08"], "name": node["f18"]["f08"]} for node in part.features],
        "next_id": part.next_id, "input_runtime_file_access_attempts": len(AUDIT.DeniedReads),
    }


def main():
    print(json.dumps(build_report(json.load(sys.stdin)), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
