from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

from AuthorCurves import digest, require, write_json


SPEC_SCHEMA = "kit.sw2026.nested-assembly-source-specs.v1"
DECK_SCHEMA = "kit.sw2026.nested-assembly-source-deck.v1"
SOURCE_LOCK = "8f79ed2aa8559b7186f414330b495ce50c4fa3612f69d421bbd7bc83037ca417"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL_SHA = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
TOOL_FILES = (
    "NestedAssemblySourcePlan.py", "AuthorNestedAssemblySources.py", "AuthorAssemblySources.py", "AuthorCurves.py",
    "InspectCircleSketch.py", "InspectFresh.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py",
)
WIDTH, HEIGHT = (0.04, 0.02)
PARAMETERS = ("D1@Sketch1", "D2@Sketch1", "D1@Boss-Extrude1")
IDENTITY = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def checked(path, sha, owner=None):
    actual = path.resolve(strict=True)
    require(actual.is_file() and not path.is_symlink() and (owner is None or actual.is_relative_to(owner)), "invalid nested source input path")
    require(valid_sha(sha) and digest(actual) == sha, f"nested source input hash differs for {path.name}")
    return actual


def model_name(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,47}", value) is not None


def placement_matrix(placement):
    require(set(placement) == {"axis", "angle_deg", "translation_m"}, "unexpected nested placement fields")
    axis = placement["axis"]
    require(axis in ("x", "y", "z") and finite(placement["angle_deg"]), "invalid rigid rotation")
    t = placement["translation_m"]
    require(isinstance(t, list) and len(t) == 3 and all(map(finite, t)), "invalid nested translation")
    theta = math.radians(placement["angle_deg"])
    c, s = math.cos(theta), math.sin(theta)
    rotation = {"x": [1, 0, 0, 0, c, s, 0, -s, c], "y": [c, 0, -s, 0, 1, 0, s, 0, c],
                "z": [c, s, 0, -s, c, 0, 0, 0, 1]}[axis]
    return [*rotation, *t, 1.0, 0.0, 0.0, 0.0]


def placed_point(point, matrix):
    return [math.fsum(point[i] * matrix[i * 3 + j] for i in range(3)) + matrix[9 + j] for j in range(3)]


def compose(local, owner):
    basis = [math.fsum(local[i * 3 + k] * owner[k * 3 + j] for k in range(3)) for i in range(3) for j in range(3)]
    return [*basis, *placed_point(local[9:12], owner), 1.0, 0.0, 0.0, 0.0]


def matches_transform(observed, expected):
    return len(observed) == len(expected) == 16 and all(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12) for a, b in zip(observed, expected, strict=True))


def part_geometry(depth):
    return {"body_count": 1, "volume": WIDTH * HEIGHT * depth, "area": 2 * (WIDTH * HEIGHT + WIDTH * depth + HEIGHT * depth),
            "com": [0.0, 0.0, depth / 2]}


def expected_tree(case, *, owner=None, edited=False):
    parts = {row["name"]: row["depth_m"] for row in case["parts"]}
    assemblies = {row["name"]: row["occurrences"] for row in case["assemblies"]}
    if edited:
        parts[case["edit"]["part"]] = case["edit"]["depth_m"]
    leaves = []
    count = 0

    def expand(name, world):
        nonlocal count
        rows = []
        for index, row in enumerate(assemblies[name]):
            count += 1
            require(count <= 12, "nested designs admit at most 12 expanded occurrences")
            target = row["target"]
            local = placement_matrix(row["placement"])
            transform = compose(local, world)
            entry = {"ordinal": index, "target": target, "local": local, "world": transform}
            if target in parts:
                geometry = part_geometry(parts[target])
                leaves.append(geometry | {"com": placed_point(geometry["com"], transform)})
                entry.update(kind="part", children=[])
            else:
                entry.update(kind="assembly", children=expand(target, transform))
            rows.append(entry)
        return rows

    selected = owner or case["assemblies"][-1]["name"]
    children = expand(selected, IDENTITY)
    volume = math.fsum(leaf["volume"] for leaf in leaves)
    return {"owner": selected, "children": children, "total_occurrences": count, "body_count": len(leaves), "volume": volume,
            "area": math.fsum(leaf["area"] for leaf in leaves),
            "com": [math.fsum(leaf["volume"] * leaf["com"][axis] for leaf in leaves) / volume for axis in range(3)]}


def validate_case(case):
    require(set(case) == {"name", "split", "parts", "assemblies", "edit"} and model_name(case["name"]), "unexpected nested source case")
    require(case["split"] in ("discovery", "heldout"), "unexpected source split")
    parts, assemblies = case["parts"], case["assemblies"]
    require(1 <= len(parts) <= 3 and 2 <= len(assemblies) <= 4, "nested cohort requires one to three part definitions and two to four assembly definitions")
    known = set()
    references = set()
    for row in parts:
        name, depth = row["name"], row["depth_m"]
        require(set(row) == {"name", "depth_m"} and model_name(name) and name.casefold() not in known and finite(depth) and depth > 0, "invalid rectangular part definition")
        known.add(name.casefold())
    allowed = {row["name"] for row in parts}
    for assembly in assemblies:
        name = assembly["name"]
        require(set(assembly) == {"name", "occurrences"} and model_name(name) and name.casefold() not in known and
                1 <= len(assembly["occurrences"]) <= 6, "invalid nested assembly definition")
        instances = []
        for entry in assembly["occurrences"]:
            target = entry["target"]
            require(set(entry) == {"target", "placement"} and target in allowed, "definitions must be ordered bottom-up with unique names")
            pose = placement_matrix(entry["placement"])
            require(not any(child == target and matches_transform(existing, pose) for child, existing in instances), "two sibling placements are indistinguishable")
            instances.append((target, pose))
            references.add(target)
        allowed.add(name)
        known.add(name.casefold())
    require(references == allowed - {assemblies[-1]["name"]}, "every dependency must be reachable from the final root")
    edit = case["edit"]
    originals = {row["name"]: row["depth_m"] for row in parts}
    require(set(edit) == {"part", "depth_m"} and edit["part"] in originals and finite(edit["depth_m"]) and edit["depth_m"] > 0 and
            edit["depth_m"] != originals[edit["part"]], "nested source requires a changed driving depth on one leaf document")
    expected_tree(case)
    return case


def cases_from(path, split):
    data = json.loads(path.read_bytes())
    prefixes = ("N01", "N02") if split == "discovery" else ("N03", "N04")
    require(set(data) == {"schema", "cases"} and data["schema"] == SPEC_SCHEMA and len(data["cases"]) == 2, "unexpected nested source case pack")
    cases = tuple(validate_case(case) for case in data["cases"])
    require(all(case["split"] == split and case["name"].startswith(prefix) for case, prefix in zip(cases, prefixes, strict=True)), "case order or source split differs")
    return cases


def load_deck(path, sha):
    root = path.parent
    require(path.name == "Deck.json" and checked(path, sha, root) == path, "nested deck manifest is not pinned")
    deck = json.loads(path.read_bytes())
    require(deck["schema"] == DECK_SCHEMA and deck["control_sha256"] == CONTROL_SHA and deck["oracle_sha256"] == ORACLE and
            deck["reference_source_lock_sha256"] == SOURCE_LOCK and deck["heldout_results_sealed"] is True,
            "unexpected nested source deck provenance")
    tools = (root / "Tools").resolve(strict=True)
    require(Path(__file__).resolve().parent == tools and tools.is_relative_to(root) and set(deck["tool_hashes"]) == set(TOOL_FILES), "run the prescribed frozen tools")
    for name, sha in deck["tool_hashes"].items():
        checked(tools / name, sha, tools)
    inputs = (root / "Inputs").resolve(strict=True)
    require(inputs.is_relative_to(root), "nested source input directory escaped its deck")
    discovery = checked(inputs / "Discovery.json", deck["discovery_sha256"], inputs)
    heldout = checked(inputs / "Holdouts.json", deck["holdouts_sha256"], inputs)
    source = checked(inputs / "Seed.SLDPRT", CONTROL_SHA, inputs)
    return deck, discovery, heldout, source


def prepare(args):
    tools = Path(__file__).resolve().parent
    checkout = tools.parents[2]
    root = args.deck.resolve()
    require(not root.exists() and root.parent.is_dir() and not root.is_relative_to(checkout), "choose an unused private nested source deck")
    discovery = checked(args.discovery, args.discovery_sha256)
    heldout = checked(args.holdouts, args.holdouts_sha256)
    source = checked(args.seed, CONTROL_SHA)
    require(discovery != heldout and not heldout.is_relative_to(checkout) and not source.is_relative_to(checkout), "keep held-out requests and native seed private")
    cases_from(discovery, "discovery")
    root.mkdir()
    (root / "Inputs").mkdir()
    (root / "Tools").mkdir()
    for path, name, sha in ((discovery, "Discovery.json", args.discovery_sha256), (heldout, "Holdouts.json", args.holdouts_sha256), (source, "Seed.SLDPRT", CONTROL_SHA)):
        target = root / "Inputs" / name
        copyfile(path, target)
        checked(target, sha, root)
    hashes = {}
    for name in TOOL_FILES:
        target = root / "Tools" / name
        copyfile(tools / name, target)
        hashes[name] = digest(target)
    path = root / "Deck.json"
    write_json(path, {"schema": DECK_SCHEMA, "discovery_sha256": args.discovery_sha256, "holdouts_sha256": args.holdouts_sha256,
                      "reference_source_lock_sha256": SOURCE_LOCK, "control_sha256": CONTROL_SHA, "oracle_sha256": ORACLE,
                      "heldout_results_sealed": True, "tool_hashes": hashes})
    sha = digest(path)
    subprocess.run([sys.executable, "-B", str(root / "Tools" / "AuthorNestedAssemblySources.py"), str(path), "--deck-sha256", sha, "--verify-only"],
                   check=True, capture_output=True, timeout=25)
    return {"deck": str(path), "deck_sha256": sha, "tool_hashes": hashes}


def main():
    parser = argparse.ArgumentParser(description="Freeze a private disclosed and held-out nested assembly source deck")
    for name in ("discovery", "holdouts", "seed", "deck"):
        parser.add_argument(name, type=Path)
    for name in ("--discovery-sha256", "--holdouts-sha256"):
        parser.add_argument(name, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
