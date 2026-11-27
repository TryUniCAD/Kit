import dataclasses
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import traceback

from convert import open_document
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    revision = sys.argv[3]
    if output.exists():
        raise ValueError("output must be unused")
    output.mkdir(parents=True)
    source_manifest = "re/Fusion/Reconstruction/CircularSpans/Manifest.json"
    raw_manifest = subprocess.check_output(["git", "show", f"{revision}:{source_manifest}"], cwd=root)
    manifest = json.loads(raw_manifest)
    report = {
        "scope": "same-document typed reconstruction qualification preparation; native acceptance not established",
        "revision": revision,
        "python_version": platform.python_version(),
        "python_executable_sha256": digest(Path(sys.executable).resolve().read_bytes()),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "source_manifest": source_manifest,
        "source_manifest_sha256": digest(raw_manifest),
        "models": False,
        "cad_runtime": False,
        "rows": [],
    }
    for sample in manifest["samples"]:
        case_name = sample["group"] + "_" + sample["name"]
        case_path = output / case_name
        case_path.mkdir()
        row = {"case": case_name, "source": sample["file"], "group": sample["group"], "side_mode": sample["side_mode"], "expected_source_sha256": sample["sha256"], "checks": {}}
        try:
            source = subprocess.check_output(["git", "show", f"{revision}:{sample['file']}"], cwd=root)
            row["source_sha256"] = digest(source)
            if row["source_sha256"] != sample["sha256"]:
                raise ValueError("committed source disagrees with manifest")
            row["checks"]["committed_hash"] = True
            model = ReadDocument(source)
            candidate = EmitParsed(model)
            candidate_path = case_path / "Candidate.f3d"
            candidate_path.write_bytes(candidate)
            row["candidate"] = str(candidate_path.relative_to(output))
            row["candidate_sha256"] = digest(candidate)
            row["candidate_size"] = len(candidate)
            row["byte_identical"] = candidate == source
            rebuilt_model = ReadDocument(candidate)
            row["checks"]["complete_typed_equality"] = rebuilt_model == model
            original_document = open_document(source)
            candidate_document = open_document(candidate)
            normalized = dataclasses.replace(candidate_document, source=original_document.source)
            row["checks"]["complete_neutral_equality"] = normalized == original_document
            original_document.AssertValid()
            candidate_document.AssertValid()
            row["checks"]["both_documents_valid"] = True
            topology = candidate_document.bodies[0].topology
            observed = sample["observed"]["bodies"][0]
            row["checks"]["volume"] = math.isclose(topology.volume, observed["volume_cm3"] * 1000, rel_tol=1e-9, abs_tol=1e-8)
            row["checks"]["area"] = math.isclose(topology.surface_area, observed["area_cm2"] * 100, rel_tol=1e-9, abs_tol=1e-8)
            row["checks"]["topology_counts"] = (topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count) == (1, observed["faces"], observed["edges"], observed["vertices"])
            bounds = topology.bounding_box
            row["checks"]["bounds"] = all(math.isclose(actual, expected * 10, rel_tol=1e-9, abs_tol=1e-8) for point, wanted in ((bounds.minimum, observed["min_cm"]), (bounds.maximum, observed["max_cm"])) for actual, expected in zip((point.x, point.y, point.z), wanted, strict=True))
            (case_path / "SourceDocument.json").write_text(original_document.to_json())
            (case_path / "CandidateDocument.json").write_text(candidate_document.to_json())
            (case_path / "TypedModel.json").write_text(json.dumps(EncodeState(model), sort_keys=True, indent=2))
            (case_path / "NativeExpected.json").write_text(json.dumps(sample["observed"], sort_keys=True, indent=2))
            row["artifacts"] = {path.name: digest(path.read_bytes()) for path in sorted(case_path.iterdir())}
            row["status"] = "prepared" if all(row["checks"].values()) else "comparison_failed"
        except Exception as error:
            row["status"] = "error"
            row["error_type"] = type(error).__name__
            row["error"] = str(error)
            (case_path / "Failure.txt").write_text(traceback.format_exc())
        report["rows"].append(row)
        (output / "Receipt.json").write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps({"case": case_name, "status": row["status"], "error": row.get("error"), "checks": row["checks"]}), flush=True)
    report["summary"] = {"cases": len(report["rows"]), "prepared": sum(row["status"] == "prepared" for row in report["rows"]), "failed": sum(row["status"] != "prepared" for row in report["rows"]), "checks": sum(len(row["checks"]) for row in report["rows"]), "passing_checks": sum(value is True for row in report["rows"] for value in row["checks"].values()), "byte_identical": sum(row.get("byte_identical", False) for row in report["rows"])}
    (output / "Receipt.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report["summary"]), flush=True)


if __name__ == "__main__":
    main()
