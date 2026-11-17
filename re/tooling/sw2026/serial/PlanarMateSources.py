from __future__ import annotations

import argparse
import json
from math import isclose
from pathlib import Path

from AssemblyMates import load_mate_list, store_mate_list
from AssemblySources import CONFIG, HEADER, RESOLVED, ROOT, digest, require
from Classes import registry
from Core import DOCUMENT_VERSION_2026, Obj
from RoundTrip import PLANS, REQUIRED, one
from StringCorpus import SourceProof
from SyncedAssemblies import typed_header
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved
from convert.adapters.solidworks.Container.Container import SldprtArchive


LOCK = ROOT / "re/solidworks/v2026/heldout/AssemblyPlanarMateSourceLock01.json"
SPECS = ROOT / "re/tooling/sw2026/AssemblyMateSourceSpecs01.json"
VERSION = DOCUMENT_VERSION_2026
DISCLOSURES = ("A17PlaneCoincident", "A18PlaneDistance", "A19PlaneParallel")
MATES_LIST = CONFIG + "-MatesList"
MATE_CLASSES = {"coincident": "moMateCoincident", "distance": "moMateDistanceDim_c", "parallel": "moMateParallel"}
X, Y, Z, NEG_Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, -1.0)
PLANE_AXES = {"Right Plane": (NEG_Z, Y, X), "Top Plane": (X, NEG_Z, Y), "Front Plane": (X, Y, Z)}


def checked_archive(directory, filename, source, reg):
    path = directory / filename
    require(not path.is_symlink() and path.resolve().parent == directory, "native source escaped the disclosed directory")
    raw = path.read_bytes()
    require(len(raw) == source["native_bytes"] and digest(raw) == source["native_sha256"], "native source differs from its lock")
    archive = SldprtArchive.from_bytes(raw, path)
    report = one(path, [*REQUIRED, "Header2"], reg, {**PLANS, **reg.plans}, True, False)
    require(report["passed"] and report["sha256"] == source["native_sha256"], "native core stream round trip failed")
    config, config_map = load_config(archive.require(CONFIG), reg, VERSION, archive=archive, name=CONFIG)
    resolved, resolved_map = load_resolved(archive.require(RESOLVED), reg, VERSION, archive=archive, name=RESOLVED, seed=config_map.map_state())
    require(not config.tail and not resolved.tail and path.read_bytes() == raw, "native source was incomplete or changed")
    streams = {
        name: {field: entry[field] for field in ("bytes", "sha256", "map_base", "map_count", "proven_schemas")}
        for name, entry in report["streams"].items()
    }
    return archive, config.roots[0], resolved.roots, resolved_map.map_state(), streams


def axis_values(value):
    return tuple(value[key] for key in ("x", "y", "z"))


def transform_axes(transform):
    if not transform["has_matrix"]:
        return X, Y, Z
    matrix = transform["f08"]
    return tuple(tuple(matrix[f"m{row * 3 + column}"] for column in range(3)) for row in range(3))


def dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def near(first, second):
    return all(isclose(a, b, rel_tol=0.0, abs_tol=1e-12) for a, b in zip(first, second, strict=True))


def endpoint(mate, detached, attached, occurrence, position, plane, plane_name, child_update):
    require(detached.cls == attached.cls == "moPlaneRef_w" and detached is not attached, "mate endpoint wrappers are ambiguous")
    fallback = detached["f58"]
    require(fallback.cls == "moCompRefPlane_c" and fallback["f58"].cls == "moUnitComponent_c", "the detached endpoint has no unit component")
    require(fallback["ff8"].cls == "moRefPlane_c" and fallback["ff8"]["f08"] == -1, "the detached endpoint has no anonymous plane")
    require(detached["fd0"] == attached["fd0"] and detached["fe8"] == attached["fe8"], "mate endpoint geometry differs across wrappers")
    require(all(detached[key] == 0.0 for key in ("fb0", "fb8", "fc0", "fc8")), "the detached endpoint carries unexpected surface bounds")

    target = attached["f58"]
    chain = target["f58"]
    require(target.cls == "moCompRefPlane_c" and target["ff8"] is None and chain.cls == "moChainComponent_c", "resolved mate plane has no occurrence chain")
    link, = (row["o"] for row in chain["f20"]["f08"]["f08"])
    require(link is occurrence["f4f8"] and link["f50"] is occurrence and link["f44"] == occurrence["f08"], "mate endpoint lost the occurrence backlink")
    require(target["ff0"]["f00"] == plane["f08"], "mate endpoint lost the child datum's persistent id")
    require(attached["f08"] == occurrence["f3e0"] == child_update, "mate endpoint has a stale child update stamp")
    require(attached["f74"] == mate["f08"] and attached["f78"] == attached["f7c"] == position, "mate owner or endpoint order differs")

    transform = occurrence["f360"]
    require(attached["f10"] == attached["f18"] == transform, "mate endpoint placement differs from its occurrence")
    rotation = tuple(zip(*transform_axes(transform), strict=True))
    origin = tuple(transform[key] for key in ("f58", "f60", "f68"))
    axes = tuple(tuple(dot(axis, column) for column in rotation) for axis in PLANE_AXES[plane_name])
    require(near(axis_values(attached["fd0"]), origin) and near(axis_values(attached["fe8"]), axes[2]), "mate endpoint origin or normal differs")
    inverse = attached["f100"]
    for actual, expected in zip(transform_axes(inverse), zip(*axes, strict=True), strict=True):
        require(near(actual, expected), "mate surface inverse basis differs")
    require(near((inverse[key] for key in ("f58", "f60", "f68")), (-dot(origin, axis) for axis in axes)), "mate surface inverse origin differs")
    return {
        "position": position, "occurrence_id": occurrence["f08"], "occurrence_slot": occurrence.index,
        "child_plane": plane_name, "child_plane_id": plane["f08"], "child_update": child_update,
        "detached_wrapper_slot": detached.index, "resolved_wrapper_slot": attached.index, "resolved_inverse_matches": True,
        "resolved_surface_bounds": [attached[key] for key in ("fb0", "fb8", "fc0", "fc8")],
    }


def driving_distance(mate):
    display = mate["f4b8"]
    handle, = (row["o"] for row in display["f850"])
    dimension = handle["ff0"]
    parameter = dimension["f28"]
    require(
        (display.cls, handle.cls, dimension.cls, parameter.cls) ==
        ("moDisplayDistanceDim_c", "moFeatureDimHandle_c", "ParallelPlaneDistanceDim_c", "moLengthParameter_c"),
        "the driving distance is missing its native dimension graph",
    )
    return {"display_slot": display.index, "handle_slot": handle.index, "dimension_slot": dimension.index, "parameter_slot": parameter.index, "distance_m": parameter["f58"]}


def distance_dimension(mate, request):
    driving = driving_distance(mate)
    require(mate["f4b8"]["fad0"] == driving["distance_m"] == request["distance_m"],
            "distance display or driving parameter differs from its authored value")
    return driving


def inspect_case(root, source, spec, reg):
    name = source["name"]
    directory = root / name / "author"
    require(directory.resolve() == directory, "disclosed directory must not traverse a symbolic link")
    require(source["synchronized_child"]["path_basename"] == "CohortChild.SLDPRT", "disclosed child filename differs")
    parent, model, features, resolved_map, parent_streams = checked_archive(directory, name + ".SLDASM", source, reg)
    child, child_model, child_features, _, child_streams = checked_archive(directory, "CohortChild.SLDPRT", source["synchronized_child"], reg)
    require(model.cls == "moAssembly_c" and child_model.cls == "moPart_c", "the disclosed parent or child has the wrong model class")

    group, = (node for node in features if isinstance(node, Obj) and node.cls == "moMateGroup_c")
    require(not group["f60"]["list"]["items"] and not group["f4e8"], "the resolved group already owns persisted mate rows")
    raw = parent.require(MATES_LIST)
    with reg.track_usage("load", MATES_LIST, sources=parent.streams) as load:
        (mate,), mate_map = load_mate_list(raw, reg, VERSION, resolved_map=resolved_map)
    with reg.track_usage("store", MATES_LIST) as store:
        require(store_mate_list((mate,), reg, VERSION, resolved_map=resolved_map) == raw, "mate list did not round-trip exactly")
    usage = (load.snapshot(), store.snapshot())
    require(all(stage["completed"] and not stage["missing_schemas"] for stage in usage), "mate-list schema execution was incomplete")
    provisional = sorted({name for stage in usage for name in stage["provisional_schemas"]})
    parent_streams[MATES_LIST] = {
        "bytes": len(raw), "sha256": digest(raw), "map_base": resolved_map.count,
        "map_count": mate_map.count, "proven_schemas": not provisional, "provisional_schemas": provisional,
    }

    occurrences = [row["o"] for row in model["f68"]["list"]["items"]]
    observed_fixed = [index for index, occurrence in enumerate(occurrences) if occurrence["f400"] == 4]
    require(observed_fixed == [spec["fixed_occurrence"]], "the native fixed occurrence differs from the authored anchor")
    planes = {node["f18"]["f08"]: node for node in child_features if isinstance(node, Obj) and node.cls == "moRefPlane_c"}
    child_update = typed_header(child, reg, HEADER, "moHeader_c")["f40"]
    request, = spec["mates"]
    require(mate.cls == MATE_CLASSES[request["kind"]], "native mate class differs from the authored kind")
    require([row["k"] for row in mate["f3c8"]] == list(range(len(request["planes"]))), "detached mate keys differ from the endpoint order")
    endpoints = [
        endpoint(mate, detached["o"], attached["o"], occurrences[ordinal], position, planes[plane], plane, child_update)
        for position, (detached, attached, (ordinal, plane)) in enumerate(zip(mate["f3c8"], mate["f410"], request["planes"], strict=True))
    ]
    result = {
        "name": name, "parent_sha256": source["native_sha256"], "child_sha256": source["synchronized_child"]["native_sha256"],
        "parent_streams": parent_streams, "child_streams": child_streams, "mate_class": mate.cls,
        "mate_id": mate["f08"], "mate_slot": mate.index, "resolved_group_children": 0,
        "fixed_occurrences": observed_fixed, "endpoints": endpoints,
    }
    if request["kind"] == "distance":
        result["driving_dimension"] = distance_dimension(mate, request)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify the disclosed native planar mate graphs")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    lock, specs = LOCK.read_bytes(), SPECS.read_bytes()
    custody = json.loads(lock)
    require(custody["schema"] == "kit.sw2026.planar-mate-source-lock.v1" and custody["passed"] and custody["heldout_results_sealed"], "planar mate source lock changed")
    require(custody["specs_sha256"] == digest(specs), "planar mate authoring inputs differ from the lock")
    sources = {row["name"]: row for row in custody["cases"] if row["split"] == "discovery"}
    authored = {row["name"]: row for row in json.loads(specs)["cases"] if row["split"] == "discovery"}
    require(tuple(sources) == tuple(authored) == DISCLOSURES, "the disclosed native cohort differs")
    reg = registry()
    cases = [inspect_case(args.source_root.resolve(), sources[name], authored[name], reg) for name in DISCLOSURES]
    comparisons = sum(len(row["parent_streams"]) + len(row["child_streams"]) for row in cases)
    result = {
        "schema": "kit.sw2026.planar-mate-archive-readback.v1", "passed": True,
        "source_lock_sha256": digest(lock), "specs_sha256": digest(specs),
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "mate_codec_sha256": digest(Path(__file__).with_name("AssemblyMates.py").read_bytes()),
        "core_schema_manifest_sha256": digest(json.dumps(SourceProof(), sort_keys=True).encode()),
        "stream_comparisons": comparisons, "native_acceptance": False, "heldout_payloads_read": False,
        "writer_output_count": 0, "cases": cases,
    }
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "sources": len(cases) * 2, "stream_comparisons": comparisons}))


if __name__ == "__main__":
    main()
