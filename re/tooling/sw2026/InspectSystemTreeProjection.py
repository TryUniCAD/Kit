from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker(root, path):
    sys.path.insert(0, str(root / "src"))
    from convert import open_document

    document = open_document(path, include_brep=False, include_tessellation=False)
    print(document.to_json(indent=None))


def inspect(root, path):
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--root", str(root), "--worker", str(path)],
        capture_output=True, text=True, check=False, timeout=60, cwd=root,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    sys.path.insert(0, str(root / "src"))
    from interchange import CadDocument

    return CadDocument.from_json(result.stdout), hashlib.sha256(result.stdout.encode()).hexdigest()


def check_state(root, path, tree):
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    link = ReadNativeLink(SldprtArchive.from_bytes(path.read_bytes()), 0)
    owned = {}
    for owner in link.ResolvedValue.RootsValue:
        if owner.ClassValue.NameValue not in ("moDetailCabinet_c", "moEnvFolder_c"):
            continue
        for item in owner.FieldsValue["f60"]["list"]["items"]:
            node = item["o"]
            owned[node.FieldsValue["f08"]] = (owner, node)
    members = [row for row in tree["rows"] if row["parent_id"]]
    checked = 0
    for row in members:
        native_id = row["native_object_id"]
        if native_id is None:
            assert row["state"] is row["typed_archive_owner"] is None
            continue
        owner, node = owned[native_id]
        assert row["parent_id"] == f"sldprt:feature:{owner.FieldsValue['f08']}"
        assert row["class"] == node.ClassValue.NameValue
        assert row["typed_archive_owner"]["object_index"] == node.IndexValue
        for field_name, field_value in node.FieldsValue.items():
            if type(field_value) in (str, int, float, bool, type(None)):
                assert row["state"][field_name] == field_value
                checked += 1
        if node.ClassValue.NameValue == "moNotesAreaFtrFolder_c":
            assert row["state"]["f388"]["node_value"] == node.FieldsValue["f388"].FieldsValue["f08"]
            checked += 1
    assert set(owned) == {row["native_object_id"] for row in members if row["native_object_id"] is not None}
    return checked


def shape(document):
    return [
        {
            "id": feature.id, "name": feature.name, "kind": feature.kind.value,
            "order": feature.order, "input_feature_ids": feature.input_feature_ids,
            "sketch_id": feature.sketch_id, "parameter_ids": feature.parameter_ids,
            "native_type": feature.attributes["native_type"],
        }
        for feature in document.feature_timeline
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--saved", type=Path)
    parser.add_argument("--native-receipt", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.root.resolve(), args.worker.resolve())
        return
    if any(value is None for value in (args.before, args.saved, args.native_receipt, args.output)):
        parser.error("before, saved, native-receipt and unused output are required")
    if args.output.exists():
        raise ValueError("choose an unused result path")
    native = json.loads(args.native_receipt.read_bytes())
    assert native["native_trial"]["controls_healthy"] is True
    assert native["native_trial"]["open_errors"] == native["native_trial"]["open_warnings"] == 0
    expected = [{key: row[key] for key in ("name", "type", "parent")} for row in native["native_trial"]["tree"]]
    inputs = [("before", args.before), ("saved", args.saved)]
    initial = {role: digest(path) for role, path in inputs}
    assert initial["before"] == native["sdk_build"]["generated_sha256"]
    assert initial["saved"] == native["native_trial"]["edited_native_sha256"]
    documents = []
    rows = []
    for role, path in inputs:
        document, public_sha = inspect(args.root.resolve(), path.resolve())
        graph = document.metadata["solidworks.typed_resolved_semantics"]
        tree = graph["native_tree"]
        assert tree["status"] == "ordinary_default_profile"
        measured = [{key: row[key] for key in ("name", "type", "parent")} for row in tree["rows"]]
        assert measured == expected
        (parameter,) = [parameter for parameter in document.parameters if parameter.name == "D1"]
        state = "Initial" if role == "before" else "Edited"
        assert math.isclose(parameter.value.value * 0.001, native["native_trial"]["states"][state]["depth_m"], rel_tol=1e-12, abs_tol=1e-15)
        rows.append({
            "role": role, "source_sha256": initial[role], "public_document_sha256": public_sha,
            "parametric_rows": len(document.feature_timeline), "presentation_rows": len(measured),
            "exact_tree_field_comparisons": len(measured) * 3,
            "implicit_roles": [row["owner_role"] for row in tree["rows"] if row["native_object_id"] is None],
            "persisted_child_ids": [row["native_object_id"] for row in tree["rows"] if row["parent_id"] and row["native_object_id"] is not None],
            "configuration_helpers": [{"class": helper["class"], "stored_node_id": helper["stored_node_id"], "owner_field": helper["typed_archive_owner"]["owner_field"]} for helper in tree["configuration_helpers"]],
            "persisted_scalar_and_partner_checks": check_state(args.root.resolve(), path, tree),
            "driving_depth_mm": parameter.value.value,
        })
        documents.append(document)
    assert shape(documents[0]) == shape(documents[1])
    assert initial == {role: digest(path) for role, path in inputs}
    result = {
        "schema": "kit.sw2026.sdk-system-tree-projection.v1", "passed": True,
        "cases": rows, "modeling_identity_kind_order_links_equal": True,
        "source_immutable": True, "native_receipt_sha256": digest(args.native_receipt),
        "observer_sha256": digest(Path(__file__)), "public_reader_processes": 2,
        "native_processes_started": 0, "heldout_inputs_read": 0,
        "scope": "Exact observed name/type/parent order on the disclosed generated and saved ordinary part; no runtime status or arbitrary application-default policy qualification",
        "public_writer_qualified": False, "full_native_tree_qualified": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.output), "sha256": digest(args.output), "passed": True}))


if __name__ == "__main__":
    main()
