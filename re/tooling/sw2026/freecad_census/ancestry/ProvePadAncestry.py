from argparse import ArgumentParser
from dataclasses import replace
from io import BytesIO
from json import loads
from pathlib import Path
from subprocess import check_output, run
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS = HERE.parents[2]
BASE = "4f3fe8ee989b7df7b15c9b87c29793617047e1aa"
SOURCE_TREE = "88ab3f122fc515e9ae55ca024e07f8b517b67c6b"
OWNER_PROOF = "160f60518f6e0e8a8137f90ce9171628f9908671f076e1a4f28cec870fc71ba3"
CUSTODY = "1de42ebe8bf52b8403de2e6a73fe45b45ac83484a6532230d4b379aff93ca03f"
SOURCES = {
    "C130-P01": "d1f9225bfdf31d9708fc8fc8f94261edc9479d01d6a09c720ae70c16a5aa2362",
    "C123-P01": "c965847aa2a1ba6c1bacc43ae0c911db1610e57497ab5ca19fea5e6aed33ada4",
    "C017-P01": "215d76c07e95dd13f791b404eeacd6f625a0bbefa603e3653b007a73a853184c",
}
sys.path[:0] = [
    str(value)
    for value in (
        HERE.parent,
        HERE.parents[1],
        HERE.parents[1] / "owned_pad",
        TOOLS,
        TOOLS / "attached_top_box_source",
        TOOLS / "equations",
    )
]
from ProveBlindDormant import digest, pinned, wire


def read_members(document, source_sha):
    table = {row.id: row for row in document.brep_payloads}
    source = table["freecad:native-document"]
    grip = table["freecad:native-document-binding"]
    assert len(table) == len(document.brep_payloads)
    assert source.sha256 == digest(source.data) == document.source.sha256 == source_sha
    assert grip.data == bytes.fromhex(source_sha) and digest(grip.data) == grip.sha256
    with ZipFile(BytesIO(source.data)) as packet:
        names = packet.namelist()
        assert len(names) == len(set(names))
        return {name: packet.read(name) for name in names}


def occurrences(document, split, source_plan):
    from convert.adapters.freecad.EditShape.Prism.PrismExpected import ExpectedShape
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from PadOccurrences import read_occurrences
    from PadSourceNames import BODY, SKETCH

    (sketch,) = document.sketches
    (support,) = (
        value
        for value in document.support_planes
        if value.id == sketch.support_plane_id
    )
    expected = ExpectedShape(
        support.transform,
        tuple(PlaneVector(x * 1000, y * 1000) for x, y in source_plan.VerticesValue),
        source_plan.DepthValue * 1000,
    )
    result = {
        role: read_occurrences(
            payload, source_plan.BodyId, source_plan.FeatureId, expected
        )
        for role, (payload, _) in split.items()
        if role != SKETCH
    }
    assert result[BODY][0] == document.brep
    groups = {role: row[1] for role, row in result.items()}
    for role, kinds in groups.items():
        assert tuple(len(kinds[key]) for key in ("Face", "Edge", "Vertex")) == (
            6,
            12,
            8,
        )
    return groups


def join_legacy(document, groups, owner_report):
    from convert import open_document
    from C130SourceOwners import source_owners
    from FcstdRectangleOwners01 import topology_compare
    from PadSourceNames import BODY, PAD_SHAPE, PAD_TOOL
    from ProveC130Owners import build_part
    from ProveNamedWidthDepth import FORMAT, audit_publication

    owner = source_owners(document, "C130-P01")
    part = build_part(owner, owner.body_name)
    raw = part.BytesValue
    assert digest(raw) == owner_report["named_archive"]["sha256"]
    assert {name: digest(data) for name, data in part.StreamsValue.items()} == {
        name: item["sha256"]
        for name, item in owner_report["named_archive"]["streams"].items()
    }
    native = open_document(raw, source_format=FORMAT, strict=True)
    assert native.bodies[0].name == owner.body_name
    assert native.brep is not None and not native.brep_payloads
    body_id = document.bodies[0].id
    mapped = replace(
        native.brep, bodies=(replace(native.brep.bodies[0], design_body_id=body_id),)
    )
    equality = topology_compare(document.brep, mapped, body_id)
    rows = {}
    for kind, items in groups[BODY].items():
        child, tool = groups[PAD_SHAPE][kind], groups[PAD_TOOL][kind]
        join = equality[f"{kind.lower()}_identity_map"]
        rows[kind] = [
            {
                "ordinal": ordinal,
                "role": row.role,
                "source_body_entity": row.entity_id,
                "source_pad_result_entity": pad.entity_id,
                "source_pad_tool_entity": additive.entity_id,
                "generated_neutral_entity": join[row.entity_id],
            }
            for ordinal, (row, pad, additive) in enumerate(
                zip(items, child, tool, strict=True), 1
            )
            if row.role == pad.role == additive.role
        ]
        assert len(rows[kind]) == len(items) == len(join)
    return {
        "generated_sha256": digest(raw),
        "body_and_pad_ordinals": rows,
        "stored_legacy_names": 0,
        "generation_used_source_occurrences": False,
        "publication_refusals": {
            "fcstd": audit_publication(document),
            "native_readback": audit_publication(native),
        },
    }


def duplicate_placement(payload):
    from convert.adapters.freecad.EditShape.Prism.PrismRaw import ReadPrismRaw
    from convert.Geometry.Opencascade import KIdentityLocation, LocationProduct

    raw = ReadPrismRaw(payload.data, 4, True)
    datum = next(
        index
        for index, chain in enumerate(raw.Chains)
        if index != raw.RootRef.KLocation
        and chain
        and raw.Matrix(chain) == KIdentityLocation
    )
    used = {}
    for record in raw.Records.values():
        for child in record.Children:
            used[child.RecordA] = used.get(child.RecordA, 0) + 1
    index, leaf = next(
        (identity, offset)
        for identity, record in raw.Records.items()
        if record.KindValue == b"Ed"
        for offset, child in enumerate(record.Children)
        if used[child.RecordA] > 1
    )
    old = raw.Records[index]
    children = list(old.Children)
    old_location = raw.Chains[children[leaf].KLocation]
    added = LocationProduct(raw.Chains[datum], old_location)
    assert added != old_location and raw.Matrix(added) == raw.Matrix(old_location)
    children[leaf] = replace(children[leaf], KLocation=len(raw.Chains))
    return replace(
        raw,
        Chains=[*raw.Chains, added],
        Records={**raw.Records, index: replace(old, Children=tuple(children))},
    )


def refuse_changes(document, members, split, grouped, modern):
    from CheckScopedPlainWriter import reject
    from PadOccurrences import first_occurrences
    from PadSourceNames import BODY, PAD_SHAPE, SKETCH, TABLE
    from PadSourceNames import (
        actual_geometry,
        read_body_ranges,
        read_group_rows,
        resolve_map_rows,
        sketch_roles,
    )
    from PadElementMap import parse_map
    from PadNameTable import read_string_table

    result = {
        "numeric_identity_wrong_symbolic_occurrence": reject(
            lambda: first_occurrences(duplicate_placement(split[BODY][0])),
            ValueError,
            "distinct symbolic placements collapse to one matrix",
        )
    }
    if not modern:
        return result
    table = read_string_table(members[TABLE])
    pad, root = parse_map(split[BODY][1], table)
    bad_map = replace(
        root,
        groups=(
            replace(
                root.groups[0],
                children=(
                    replace(
                        root.groups[0].children[0],
                        tag=root.groups[0].children[0].tag + 1,
                    ),
                ),
            ),
            *root.groups[1:],
        ),
    )
    result["right_geometry_wrong_pad_child_tag"] = reject(
        lambda: read_body_ranges(
            bad_map, pad, root.groups[0].children[0].tag, grouped[BODY]
        ),
        ValueError,
        "body map range does not name the actual Pad result owner",
    )
    (wire_map,) = parse_map(split[SKETCH][1], table)
    (sketch,) = document.sketches
    sketch_pos = sketch_roles(split[SKETCH][0], sketch)
    geometry = actual_geometry(sketch)
    rows = read_group_rows(wire_map, ("Edge", "Vertex"), {"Edge": 4, "Vertex": 4})
    edge = rows["Edge"]
    switched = {**rows, "Edge": (edge[1], edge[0], *edge[2:])}
    result["changing_named_wire_edges_with_equal_archive_geometry"] = reject(
        lambda: resolve_map_rows(switched, sketch_pos, geometry, table, 0, False),
        ValueError,
        "sketch named ordinal points to a foreign physical geometry",
    )
    maps = split[PAD_SHAPE][1]
    result["truncated_exact_pad_map"] = reject(
        lambda: parse_map(maps.rsplit(b"EndMap", 1)[0], table),
        ValueError,
        "truncated element map",
    )
    result["truncated_exact_string_table"] = reject(
        lambda: read_string_table(members[TABLE].splitlines(keepends=True)[0]),
        ValueError,
        "invalid element string table framing",
    )
    return result


def compact_modern(data):
    named, sketch = data.pop("actual_pad_ordinal_aliases"), data.pop(
        "actual_sketch_ordinal_aliases"
    )
    selected = {
        "Pad.Face1": named["Face"][0],
        "Pad.Face6": named["Face"][5],
        "Pad.Edge1": named["Edge"][0],
        "Pad.Edge3": named["Edge"][2],
        "Pad.Vertex1": named["Vertex"][0],
        "Sketch.Vertex1": sketch["Vertex"][0],
    }
    semantic_join = {
        key: [
            (
                row["ordinal"],
                row["physical_role"],
                [(ref["geometry_id"], ref["endpoint"]) for ref in row["aliases"]],
            )
            for row in rows
        ]
        for key, rows in named.items()
    }
    return {
        **data,
        "selected_actual_rows": selected,
        "full_decoded_pad_rows_sha256": digest(wire(named)),
        "full_decoded_sketch_rows_sha256": digest(wire(sketch)),
        "physical_role_and_seed_join_sha256": digest(wire(semantic_join)),
    }


def worker(data):
    sys.path.insert(0, str(ROOT / "src"))
    from convert import open_document
    from CheckScopedPlainWriter import WriterAudit
    from PadSourceNames import physical_shape_members, verify_modern
    from PlanFcstdCorner import plan_corner
    import C130SourceOwners

    import ProveC130Owners
    from ProveFcstdCorner import prewarm
    from VerifyLocalSketchExpr import guard_source

    case, source = data["case"], data["source"]
    expected = SOURCES[case]
    path = Path(source).resolve(strict=True)
    compact = "".join(value for value in str(path).casefold() if value.isalnum())
    assert not any(marker in compact for marker in ("heldout", "holdout", "sealed"))
    pinned(path, expected)
    reads, denied = guard_source(path, ROOT / "src")
    doc = open_document(
        path, source_format="freecad.fcstd", strict=True, include_brep=True
    )
    doc.assert_valid()
    assert len(reads) == 1 and not denied and doc.source.sha256 == expected
    prewarm()
    initial = doc.to_json(indent=None).encode()
    audit = WriterAudit(ROOT / "src", Path("unused.SLDPRT"))
    sys.addaudithook(audit.observe)
    audit.phase = "prepare"
    try:
        plan = plan_corner(doc, case).recipe
        members = read_members(doc, expected)
        modern = case != "C130-P01"
        split = physical_shape_members(doc, members, modern)
        groups = occurrences(doc, split, plan)
        negative = refuse_changes(doc, members, split, groups, modern)
        details = (
            compact_modern(verify_modern(doc, split, members, groups))
            if modern
            else join_legacy(doc, groups, data["owner_report"])
        )
        proof = {
            "source_sha256": expected,
            "source_release": doc.source.application_version,
            "source_bundle_sha256": digest(initial),
            "exact_owned_shape_sha256": {
                role: pair[0].sha256 for role, pair in split.items()
            },
            "refine": next(
                row.value.value
                for row in doc.parameters
                if row.attributes.get("freecad_path") == "Refine"
            ),
            "placed_counts": {
                role: {
                    key: {
                        "used": len(rows),
                        "raw_records": len({row.record for row in rows}),
                    }
                    for key, rows in values.items()
                }
                for role, values in groups.items()
            },
            "strict_body_owner_identity": True,
            "legacy_or_mapped": details,
            "synthetic_refusals": negative,
            "runtime_data_reads_after_intake": 0,
        }
        assert doc.to_json(indent=None).encode() == initial
    finally:
        audit.phase = "done"
    assert (
        not denied and not audit.denied and len(reads) == 1 and not audit.target_opens
    )
    pinned(path, expected)
    return proof


def isolated_worker(request):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker"),
        input=wire(request),
        capture_output=True,
        timeout=120,
    )
    if child.returncode or child.stderr:
        sys.stderr.buffer.write(child.stderr)
        raise ValueError("isolated Pad lineage observer failed")
    return loads(child.stdout)


def run_proof(inventory):
    receipt = loads(
        pinned(
            ROOT / "re/solidworks/measurements/2026/SdkC130SourceOwners01.json",
            OWNER_PROOF,
        )
    )
    assert (
        check_output(("git", "rev-parse", f"{BASE}:src"), cwd=ROOT).decode().strip()
        == SOURCE_TREE
    )
    result = {}
    for case, sha in SOURCES.items():
        (row,) = (
            item
            for item in loads(pinned(inventory, CUSTODY))["files"]
            if item["case_id"] == case
        )
        assert row["sha256"] == sha
        owner_report = receipt["c130"] if case == "C130-P01" else None
        data = {
            "case": case,
            "source": row["source_path"],
            "owner_report": owner_report,
        }
        first = isolated_worker(data)
        assert first == isolated_worker(data)
        result[case] = first
    legacy, recent, newer = result.values()
    assert not legacy["refine"] and recent["refine"] and newer["refine"]
    assert (
        legacy["exact_owned_shape_sha256"]
        == recent["exact_owned_shape_sha256"]
        == newer["exact_owned_shape_sha256"]
    )
    assert (
        recent["legacy_or_mapped"]["physical_role_and_seed_join_sha256"]
        == newer["legacy_or_mapped"]["physical_role_and_seed_join_sha256"]
    )
    return {
        "base": BASE,
        "source_tree": SOURCE_TREE,
        "inventory_sha256": CUSTODY,
        "prior_owner_receipt_sha256": OWNER_PROOF,
        "cases": result,
        "source_members_exact": 4,
        "sdk_processes": 6,
        "native_processes": 0,
        "native_symbolic_reference_publication": False,
        "whole_source_publication": False,
        "corpus_credit": 0,
        "evidence_source_sha256": {
            str(path.relative_to(ROOT)): digest(path.read_bytes())
            for path in sorted(HERE.parent.glob("*.py"))
        },
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        result = worker(loads(sys.stdin.buffer.read()))
    else:
        if args.inventory is None:
            parser.error("--inventory is required")
        result = run_proof(args.inventory)
    sys.stdout.buffer.write(wire(result))
