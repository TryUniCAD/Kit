from argparse import ArgumentParser
from codecs import lookup
from importlib import import_module
from io import BytesIO
import json
from math import cos, inf, nextafter, sin
from pathlib import Path
import platform
import subprocess
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckMeasuredPartWriter import check_custody, demand, digest, read_pinned
from CheckScopedPlainWriter import WriterAudit


def legacy_rotation(axis, angle):
    sine, cosine = sin(-0.5 * angle), cos(-0.5 * angle)
    zero = 0.0 * sine
    return (sine, zero, zero, cosine) if axis == "x" else (zero, sine, zero, cosine)


def view_rows(graph):
    result = []
    for row in graph.RootValue.FieldsValue["f9f8"]:
        view = row["o"].FieldsValue
        transform = view["f368"]
        matrix = transform["f08"] if transform["has_matrix"] else {}
        result.append((view["f358"], {key: value.hex() for key, value in matrix.items()}))
    return result


def worker(request):
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
    from convert.adapters.solidworks.Archive.Construction.Views.ViewPlans import KViewPlans
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from interchange.document.Models.DocumentModel import CadDocument

    for module in ("interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for encoding in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)
    views = import_module("convert.adapters.solidworks.Archive.Construction.Views.MakeStdViews")
    stable_rotation = views.ViewRotation
    angular_magnitude = abs(KViewPlans[3][1][0][1])
    doc = CadDocument.from_json(json.dumps(request["document"]))
    options = WriteOptions(values={"final_destination": request["expected_locator"]})
    audit = WriterAudit(ROOT / "src", ROOT / "Unpublished.SLDPRT")
    sys.addaudithook(audit.observe)

    def adjacent_rotation(axis, angle):
        x, y, z, cosine = stable_rotation(axis, angle)
        return x, y, z, nextafter(cosine, inf) if abs(angle) == angular_magnitude else cosine

    def build(rotation):
        audit.phase = "write"
        views.ViewRotation = rotation
        try:
            return PrepareNative(doc, BytesIO(), request["written_at"], options)
        finally:
            views.ViewRotation = stable_rotation
            audit.phase = "done"

    stable, legacy, adjacent = [build(r) for r in (stable_rotation, legacy_rotation, adjacent_rotation)]
    digest_stable = digest(stable.BytesValue)
    demand(digest_stable == request["candidate_sha256"], "stable output differs from native measurement")
    stable_rows, legacy_rows, adjacent_rows = (
        view_rows(ReadPartConfig(SldprtArchive.from_bytes(value.BytesValue))) for value in (stable, legacy, adjacent)
    )
    demand([name for name, _ in stable_rows] == [name for name, _ in KViewPlans], "lost an actual standard view")
    changed = [(index, key, value, adjacent_rows[index][1][key])
               for index, (_, matrix) in enumerate(stable_rows)
               for key, value in matrix.items() if value != adjacent_rows[index][1][key]]
    demand(changed == [(index, key, "-0x1.0000000000000p-48", "-0x1.ffffffffffffep-49")
                       for index, key in ((3, "m0"), (3, "m8"), (4, "m0"), (4, "m8"),
                                          (5, "m4"), (5, "m8"), (6, "m4"), (6, "m8"))],
           "adjacent cosine did not isolate the observed eight matrix words")
    changed_streams = [key for key in stable.StreamsValue
                       if stable.StreamsValue[key] != adjacent.StreamsValue[key]]
    demand(changed_streams == ["Contents/Config-0"] and not audit.denied and audit.target_opens == 0,
           "injected contrast escaped its owned stream or touched a runtime file")
    terms = {}
    for name, turns in KViewPlans:
        for axis, angle in turns:
            stable_words = " ".join(value.hex() for value in stable_rotation(axis, angle))
            legacy_words = " ".join(value.hex() for value in legacy_rotation(axis, angle))
            terms[f"{name}/{axis}"] = {"half_angle": (-0.5 * angle).hex(),
                                       "stable_quaternion_xyzw": stable_words,
                                       "legacy_word_match": legacy_words == stable_words}
    return {"role": request["role"], "locator": request["expected_locator"],
            "request_sha256": request["request_sha256"], "stable_sha256": digest_stable,
            "stable_bytes": len(stable.BytesValue), "legacy_sha256": digest(legacy.BytesValue),
            "adjacent_sha256": digest(adjacent.BytesValue), "changed_matrix_words": changed,
            "changed_streams": changed_streams, "view_count": len(stable_rows),
            "equal_legacy_views": sum(a == b for a, b in zip(stable_rows, legacy_rows, strict=True)),
            "runtime_input_reads": len(audit.denied), "rotation_terms": terms}


def supervise(native, output):
    receipt_path = ROOT / "re/solidworks/measurements/2026/SdkDefaultPartNative01.json"
    raw_receipt = receipt_path.read_bytes()
    receipt = json.loads(raw_receipt)
    epoch = check_custody(native, receipt)
    results = []
    for row in receipt["builds"]:
        role = row["role"]
        request = read_pinned(native / role / "SdkRequest.json", row["request_sha256"])
        demand(request["written_at"] == epoch, "request timestamp differs from measured epoch")
        request |= {"role": role, "request_sha256": row["request_sha256"], "candidate_sha256": row["candidate_sha256"]}
        run = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=json.dumps(request),
                             capture_output=True, text=True, check=False, timeout=90)
        demand(run.returncode == 0 and not run.stderr, run.stdout + run.stderr)
        results.append(json.loads(run.stdout))
    terms = results[0].pop("rotation_terms")
    changed = results[0].pop("changed_matrix_words")
    demand(all(row.pop("rotation_terms") == terms for row in results[1:]),
           "standard rotation terms varied with the chosen model")
    demand(all(row.pop("changed_matrix_words") == changed for row in results[1:]),
           "adjacent matrix word contrast varied with the chosen model")
    source = ROOT / "src/convert/adapters/solidworks/Archive/Construction/Views"
    paths = [HERE, *(source / path for path in ("ViewPlans.py", "ViewRotation.py", "RoundViewSeries.py",
                                                "MultiplyQuat.py", "ViewMatrix.py", "MakeStdViews.py", "MakeViewNode.py"))]
    contrast = {"addresses": [f"Config-0/f9f8/{index}/o/f368/f08/{key}" for index, key, _, _ in changed],
                "canonical_binary64_hex": changed[0][2], "adjacent_binary64_hex": changed[0][3]}
    evidence = {"schema": "kit.sw2026.standard-view-rounding-proof.v1", "platform": platform.system(),
                "architecture": platform.machine(), "python": platform.python_version(), "cases": results,
                "rotation_terms": terms, "matrix_contrast": contrast,
                "native_processes_started": 0, "measured_epoch": epoch,
                "prior_native_report_sha256": digest(raw_receipt), "prior_native_terminal_sha256": receipt["native_result_sha256"],
                "source_sha256": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in paths}}
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(evidence, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(digest(output.read_bytes()))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--native", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
    elif args.native is None or args.output is None:
        parser.error("--native and --output are required")
    else:
        supervise(args.native, args.output)
