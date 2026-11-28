from argparse import ArgumentParser
from ast import Attribute, Call, Constant, parse, walk
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from math import isclose, prod
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from AuditArchiveCorpus import ROOT, PLANS, codec_identity, measure_archive, registry, require
from AuditKeywordCorpus import inspect as inspect_keywords
from convert import open_document


PACKAGE = ROOT / "re/solidworks/FeatureLadderRecovery"
MANIFEST = "d9df29c43e811c1e4d1e7b5071a84a110d1ed5afa06921135396f851f82a1c84"
PLANES = frozenset(("Front Plane", "Top Plane", "Right Plane"))
AXES = ("x", "y", "z")


def checked(relative, expected):
    path = PACKAGE / relative
    require(path.resolve(strict=True) == path and path.is_relative_to(PACKAGE),
            "recovered ladder member is indirect or outside the corpus")
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, "recovered ladder member differs from its manifest")
    return data


def selected_plane(program):
    names, = tuple(
        tuple(node.args[index].value for index in (0, 1))
        for node in walk(parse(program))
        if isinstance(node, Call) and isinstance(node.func, Attribute)
        and node.func.attr == "SelectByID2" and len(node.args) >= 2
        and all(isinstance(node.args[index], Constant) for index in (0, 1))
        and node.args[1].value == "PLANE"
    )
    require(names[0] in PLANES, "the captured sketch is not a principal-plane rectangle")
    return names[0]


def bounds(document):
    body, = document.bodies
    box = body.topology.bounding_box
    require(box is not None, "strict rectangle read lost its world bounds")
    return tuple(tuple(getattr(point, axis) for axis in AXES) for point in (box.minimum, box.maximum))


def close(value, target):
    return isclose(value, target, rel_tol=1e-8, abs_tol=1e-6)


def measure_geometry(raw, expected, plane):
    document = open_document(BytesIO(raw), source_format="solidworks.sldprt", strict=True)
    design = open_document(BytesIO(raw), source_format="solidworks.sldprt", strict=True, include_brep=False)
    document.assert_valid()
    design.assert_valid()
    sketch, = document.sketches
    (support,) = tuple(value for value in document.support_planes if value.id == sketch.support_plane_id)
    low, high = bounds(document)
    center = [(left + right) / 2 for left, right in zip(low, high, strict=True)]
    target = [value * 1000 for value in expected["centroid_m"]]
    edges = [right - left for left, right in zip(low, high, strict=True)]
    area = 2 * sum(edges[i] * edges[j] for i, j in ((0, 1), (0, 2), (1, 2)))
    (boss,) = tuple(value for value in document.feature_timeline if value.kind.value == "extrusion")
    (driver,) = tuple(value for value in document.parameters if value.owner_id == boss.id and value.name == "D1")
    depth = expected["parameters_mm"]["depth"]
    return {
        "plane": support.name,
        "plane_matches": support.name == plane,
        "design_only_matches": design.sketches == document.sketches and bounds(design) == (low, high)
            and design.parameters == document.parameters and design.feature_timeline == document.feature_timeline,
        "bounds_mm": [low, high],
        "centroid_matches": all(close(a, b) for a, b in zip(center, target, strict=True)),
        "volume_matches": close(prod(edges), expected["volume_m3"] * 1e9),
        "area_matches": close(area, expected["area_m2"] * 1e6),
        "depth_driver_matches": boss.sketch_id == sketch.id and driver.value.unit == "mm"
            and close(driver.value.value, depth) and driver.value == boss.definition.length,
        "full_brep_present": document.brep is not None,
        "design_only_brep_absent": design.brep is None,
        "editable_sketch_parameters": sum(value.owner_id == sketch.id for value in document.parameters),
        "feature_kinds": [value.kind.value for value in document.feature_timeline],
    }


def audit(revision):
    codec = codec_identity(revision)
    manifest = json.loads(checked("Manifest.json", MANIFEST))
    assets = {value["path"]: value["sha256"] for value in manifest["artifacts"]}
    reg = registry()
    plans = {**PLANS, **reg.plans}
    rows = {}
    for case in manifest["cases"]:
        require(case["capture_status"] == "complete_controlled_batch", "incomplete native ladder batch")
        program = checked(case["capture_program"], case["capture_program_sha256"])
        plane = selected_plane(program)
        name = case["case"]
        truth_path = f"Cases/{name}/GroundTruth.json"
        truth = {value["case"]: value for value in json.loads(checked(truth_path, assets[truth_path]))["cases"]}
        require(set(truth) == {"control-before", "variation", "control-after"}, "incomplete native control bracket")
        for member in case["files"]:
            path = member["native_path"]
            role = Path(path).stem
            expected = truth[role]
            input_digest = member["source_sha256"]
            require(path == f"Cases/{name}/{role}.SLDPRT" and assets[path] == input_digest == expected["sha256"],
                    "recovered source does not join the independent native measurement")
            raw = checked(path, input_digest)
            rows[path] = {
                "geometry": measure_geometry(raw, expected, plane),
                "archive": measure_archive(raw, reg, plans, assembly=False),
                "keywords": inspect_keywords(raw),
            }
    require(len(rows) == 111 and codec_identity(revision) == codec, "recovered ladder scope or codec changed")
    return {
        "schema": "kit.sw2026.recovered-cuboid-ladder-audit.v1",
        "archive_codec_revision": revision,
        "archive_codec_git_objects": codec,
        "manifest_sha256": MANIFEST,
        "tools_sha256": {
            name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("AuditRecoveredLadder.py", "AuditArchiveCorpus.py", "AuditKeywordCorpus.py")
        },
        "native_controlled_batches": 37,
        "heldout_inputs_read": 0,
        "native_processes_started": 0,
        "native_writer_outputs": 0,
        "rows": rows,
    }


def summary(data):
    results = data["rows"]
    shape = Counter()
    keywords = Counter()
    by_stream = {}
    for row in results.values():
        geometry = row["geometry"]
        shape.update({"files": 1, **{key: value for key, value in geometry.items()
                                  if key.endswith(("_matches", "_present", "_absent"))}})
        index = row["keywords"]
        keywords.update({"attempted": 1, "ordinary_framing": index["ordinary_framing"],
                         "typed_exact": index["compact_typed_reassembly"] or index["spaced_typed_reassembly"]})
        for name, stream in row["archive"]["streams"].items():
            totals = by_stream.setdefault(name, Counter())
            totals["attempted"] += 1
            totals["typed_exact"] += stream["proven_typed_exact"]
            totals["exact_bytes"] += stream["exact_without_tail"]
    return {"geometry": shape, "streams": by_stream, "keywords": keywords}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("revision")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit(args.revision)
    payload = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(payload)
    print(json.dumps(summary(report) | {"receipt_sha256": sha256(payload).hexdigest()}, sort_keys=True))
