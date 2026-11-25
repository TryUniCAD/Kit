from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import replace
from pathlib import Path


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "re" / "automation"))
    from convert import open_document
    from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
    from convert.adapters.Fusion.State.EncodeState import EncodeState
    from convert.Formats.Fusion.ContainerCodec.Preview.EmitPreview import EmitPreview
    from EncoderRoundTrip.Fusion import generate_candidate, make_cuboid

    adapter_path = root / "re/automation/EncoderRoundTrip/Fusion.py"
    adapter_hash = digest(adapter_path.read_bytes())
    checks = []
    locator = "00000000-0000-4000-8000-000000000001"
    written_at = 1795564800
    seed = make_cuboid("Boundary smoke cuboid", 17.25, 23.5, 31.75)
    seed_json = output / "Source.json"
    seed_json.write_text(seed.to_json(), encoding="utf-8")
    source_hash = digest(seed_json.read_bytes())
    persisted = type(seed).from_json(seed_json.read_text(encoding="utf-8"))

    def record(name: str, **values: object) -> None:
        checks.append({"name": name, "status": "passed", **values})

    def reject(name: str, source: Path, edit: dict | None = None) -> None:
        before = digest(source.read_bytes())
        try:
            document = open_document(source)
            generate_candidate(document, edit, native_locator=locator, written_at=written_at)
        except (ValueError, TypeError) as error:
            assert digest(source.read_bytes()) == before, name
            diagnostic = str(error).replace(str(output), "<output>").replace(str(root), "<root>")
            record(name, source_name=source.name, source_sha256=before, error_type=type(error).__name__, diagnostic=diagnostic)
        else:
            raise AssertionError(name + " unexpectedly generated output")

    def summary(document: object) -> dict:
        assert len(document.bodies) == 1
        body = document.bodies[0]
        assert body.topology.solid_count == 1
        return {
            "body_count": len(document.bodies),
            "solid_count": body.topology.solid_count,
            "volume_mm3": body.topology.volume,
            "feature_count": len(document.feature_timeline),
            "sketch_count": len(document.sketches),
            "parameter_count": len(document.parameters),
            "metadata_keys": sorted(document.metadata),
        }

    original = generate_candidate(persisted, native_locator=locator, written_at=written_at)
    repeated = generate_candidate(persisted, native_locator=locator, written_at=written_at)
    assert original == repeated
    original_path = output / "Original.f3d"
    original_path.write_bytes(original)
    strict = open_document(original_path)
    assert set(strict.metadata) == {"fusion.native_state"}
    record("pinned_authored_generation", source_sha256=source_hash, sha256=digest(original), observation=summary(strict))

    native_json = output / "Native.json"
    native_json.write_text(strict.to_json(), encoding="utf-8")
    native = type(seed).from_json(native_json.read_text(encoding="utf-8"))
    replay = generate_candidate(native, native_locator=locator, written_at=written_at)
    assert replay == generate_candidate(native, native_locator=locator, written_at=written_at)
    replay_doc = open_document(replay, source_format="f3d")
    assert replace(native, source=replay_doc.source, metadata=replay_doc.metadata) == replay_doc
    record("persisted_native_deterministic_reconstruction", source_sha256=digest(native_json.read_bytes()), sha256=digest(replay))

    relabeled = generate_candidate(
        native, native_locator="DifferentCandidate.f3d", written_at=written_at
    )
    assert relabeled != replay
    alternate = output / "Alternate.f3d"
    alternate.write_bytes(relabeled)
    assert summary(open_document(alternate)) == summary(strict)
    record("native_reconstruction_uses_requested_locator", sha256=digest(relabeled))

    changed = generate_candidate(
        native,
        {"dimension": "depth", "value_mm": 43.125},
        native_locator=locator,
        written_at=written_at,
    )
    changed_path = output / "Changed.f3d"
    changed_path.write_bytes(changed)
    changed_doc = open_document(changed_path)
    changed_summary = summary(changed_doc)
    expected_volume = 17.25 * 23.5 * 43.125
    assert math.isclose(changed_summary["volume_mm3"], expected_volume, rel_tol=1e-12)
    lengths = {parameter.id: parameter.value.value for parameter in changed_doc.parameters}
    assert lengths["length"] == 43.125 and lengths["along"] == 43.125
    assert lengths["width"] == 17.25 and lengths["depth"] == 23.5
    assert digest(seed_json.read_bytes()) == source_hash
    record("persisted_native_driving_edit", source_sha256=digest(native_json.read_bytes()), observation=changed_summary, sha256=digest(changed))

    reject(
        "unsupported_parameter",
        seed_json,
        {"dimension": "width", "value_mm": 19.0},
    )
    for name, value in (("NoOpEdit", 31.75), ("BooleanEdit", True), ("NegativeEdit", -1.0)):
        reject(name, seed_json, {"dimension": "depth", "value_mm": value})

    altered = replace(
        seed,
        parameters=(
            replace(seed.parameters[0], value=replace(seed.parameters[0].value, value=34.0)),
            *seed.parameters[1:],
        ),
    )
    stale = output / "Stale.json"
    stale.write_text(altered.to_json(), encoding="utf-8")
    reject("stale_authoring_contract", stale)
    native_stale = output / "NativeStale.json"
    native_stale.write_text(
        replace(native, parameters=altered.parameters).to_json(), encoding="utf-8"
    )
    reject("stale_native_contract", native_stale)
    no_contract = output / "NoContract.json"
    no_contract.write_text(replace(seed, metadata={}).to_json(), encoding="utf-8")
    reject("missing_contract", no_contract)

    old_data = json.loads(seed.to_json())
    del old_data["materials"]
    old_json = output / "Old.json"
    old_json.write_text(json.dumps(old_data), encoding="utf-8")
    reject("historical_json_without_materials", old_json)

    legacy_data = json.loads(native.to_json())
    model_fields = legacy_data["metadata"]["fusion.native_state"]["model"]["fields"]
    model_fields.pop("Forms", None)
    model_fields.pop("Meshes", None)
    legacy_json = output / "LegacyDefaults.json"
    legacy_json.write_text(json.dumps(legacy_data), encoding="utf-8")
    legacy = open_document(legacy_json)
    assert generate_candidate(legacy, native_locator=locator, written_at=written_at) == replay
    record("historical_empty_state_defaults", source_sha256=digest(legacy_json.read_bytes()))

    typed_model = CheckContract(native.metadata["fusion.native_state"], "model")
    custom_preview = replace(typed_model.Previews[0], Payload=EmitPreview(1, 1, bytes((7, 11, 13, 255))))
    extra_model = replace(typed_model, Previews=(custom_preview, *typed_model.Previews[1:]))
    preview_json = output / "CustomPreview.json"
    preview_json.write_text(
        replace(native, metadata={"fusion.native_state": {"version": 1, "model": EncodeState(extra_model)}}).to_json(),
        encoding="utf-8",
    )
    reject("native_external_preview_no_edit", preview_json)
    reject("native_external_preview_with_edit", preview_json, {"dimension": "depth", "value_mm": 43.125})

    for name, contract in (
        ("UnsupportedVersion", {**dict(native.metadata["fusion.native_state"]), "version": 99}),
        ("ExtraField", {**dict(native.metadata["fusion.native_state"]), "unexpected": True}),
    ):
        bad_json = output / (name + ".json")
        bad_json.write_text(
            replace(native, metadata={"fusion.native_state": contract}).to_json(),
            encoding="utf-8",
        )
        reject(name, bad_json)

    assert digest(adapter_path.read_bytes()) == adapter_hash, "Adapter changed during smoke"
    report = {
        "status": "deterministic_codec_checks_passed_native_acceptance_unmeasured",
        "python_version": sys.version.split()[0],
        "adapter_sha256": adapter_hash,
        "adapter_unchanged_during_run": True,
        "script_sha256": digest(Path(__file__).read_bytes()),
        "vendor_loadable": False,
        "application_usable": False,
        "native_acceptance": "unmeasured",
        "vendor_runtime_invoked": False,
        "checks": checks,
        "source_artifacts": {
            artifact.name: digest(artifact.read_bytes()) for artifact in sorted(output.glob("*.json"))
        },
    }
    (output / "Report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks_passed": len(checks)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
