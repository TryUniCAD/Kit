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
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved


def require(check, message):
    if not check:
        raise ValueError(message)


def verify_anchor(archive, rules, mode):
    config_name = "Contents/Config-0"
    resolved_name = config_name + "-ResolvedFeatures"
    config, seed = load_config(archive.require(config_name), rules, DOCUMENT_VERSION_2026, archive=archive, name=config_name)
    resolved, terminal = load_resolved(archive.require(resolved_name), rules, DOCUMENT_VERSION_2026,
                                       archive=archive, name=resolved_name, seed=seed.map_state())
    require(not config.tail and not resolved.tail, "unread bytes in generated anchor graph")
    model, = config.roots
    profile, = [node for node in resolved.roots if node.cls == "moProfileFeature_c"]
    origin, = [node for node in resolved.roots if node.cls == "moOriginProfileFeature_c"]
    sketch = profile["pd_f80"]
    relations = sketch["dims"]["log_g2"]
    if mode is None:
        require(not relations, "unanchored rectangle acquired a coincidence")
        return seed.count, terminal.count, len(relations)
    require((mode, len(relations)) in (("corner", 1), ("center", 3)), "unexpected rectangle coincidence topology")
    external, = [item["point"] for item in sketch["points"] if item["kind"] == 1]
    wrapper = external["ext"]["f08"]
    selected = wrapper["f58"]
    require(selected["ff0"]["f00"] == origin["f08"] and selected["f0f8"]["idx"] == 0
            and selected["f58"]["owner"] is model and profile["pd_f78"]["f58"]["owner"] is model
            and origin["pd_f78"]["f58"]["owner"] is model,
            "external point does not select its generated document origin")
    require(selected["f100"] == origin["pd_f80"]["points"][0]["point"]["f08"],
            "external point did not retain the origin's persistent mark")
    relation = relations[-1]["d"]
    require(relation["f80"] == 9 and sketch["points"][relation["h1"]["idx"]]["point"] is external
            and sketch["points"][relation["h2"]["idx"]]["point"]["pos"] == external["pos"] == {"x": 0.0, "y": 0.0},
            "generated logical relation lost ownership or point coordinates")
    if mode == "center":
        center_slot = relation["h2"]["idx"]
        center = sketch["points"][center_slot]["point"]
        require(center["fe4"] == 1 and center["fe8"] == 0 and center["f20"] == 3,
                "generated center must own exactly its three coincidence relations")
        diagonals = {index for index, row in enumerate(sketch["lines"]) if row["line"]["f54"] & 8}
        require(len(sketch["lines"]) == 6 and len(diagonals) == 2, "expected four body edges and two construction diagonals")
        for row in relations[:-1]:
            link = row["d"]
            require(link["f80"] == 9 and link["h1"].cls == "sgPointHandle" and link["h1"]["idx"] == center_slot
                    and link["h2"].cls == "sgLineHandle" and link["h2"]["idx"] in diagonals,
                    "center relation must own one actual construction diagonal")
            line = sketch["lines"][link["h2"]["idx"]]["line"]
            first, second = (sketch["points"][line[key]]["point"]["pos"] for key in ("fc8_s", "fcc_s"))
            require(all(first[axis] == -second[axis] for axis in ("x", "y")) and line["f20"] == 1,
                    "construction diagonal lost opposite endpoints or its center relation")
            diagonals.remove(link["h2"]["idx"])
    return seed.count, terminal.count, len(relations)


def build(request):
    for name in ("utf-16-le", "utf-8", "latin-1"):
        codecs.lookup(name)
    rules = registry()
    AUDIT.BeginBuild()
    part = construct_part(registry=rules, **request)
    payload = build_sldprt(part.streams)
    archive = SldprtArchive.from_bytes(payload)
    require(archive.streams == part.streams, "container lost generated anchor streams")
    config_count, resolved_count, relations = verify_anchor(archive, rules, request.get("rectangle_anchor"))
    streams = {}
    for name, content in part.streams.items():
        if name.startswith("swXmlContents/"):
            continue
        roundtrip = stream_roundtrip(archive, name, rules, {**PLANS, **rules.plans}, linked=True)
        require(roundtrip["passed"], f"generated anchor stream did not round-trip: {name}")
        streams[name] = {"sha256": sha256(content).hexdigest(), "bytes": len(content)}
    require(not AUDIT.DeniedReads, "input read attempted inside the rectangle builder")
    return {"schema": "kit.sw2026.rectangle-anchor-guarded-build.v1",
            "native": {"sha256": sha256(payload).hexdigest(), "bytes": len(payload), "artifact_base64": b64encode(payload).decode("ascii")},
            "streams": streams, "linked_config_counter": config_count, "linked_resolved_counter": resolved_count,
            "new_origin_relations": relations, "input_runtime_file_access_attempts": 0,
            "writer_output_count": 1, "native_acceptance": False}


if __name__ == "__main__":
    print(json.dumps(build(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
