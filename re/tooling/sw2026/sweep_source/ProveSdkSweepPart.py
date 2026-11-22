from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from math import pi
from ntpath import join
from pathlib import Path
from subprocess import check_output
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE)]
from AuditColdSweep import inspect_output
from AuditSweepArchive import guard_runtime
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import BuildSweepPart
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from SweepModel import dimensions, require, validate_spec


SPEC = "e62d1d09ac26cc0ae9538a846b0800023441403b5d04ac432a8f6b1da8e71023"
NATIVE = "380ead8ff07a9337bd0df87d32eb92e49529e0579c15449767a5ee26e53dd512"
LOCATOR = r"C:\KitSweepCold02\Packet\Candidates"
MEASURED = ROOT / "re" / "solidworks" / "measurements" / "2026" / "OrdinarySweepColdNativeDisclosed02.json"


def checked_json(path, expected):
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, f"unexpected disclosed metadata: {path.name}")
    return json.loads(data)


def expected_refusal(call, diagnostic, error=ValueError):
    try:
        call()
    except error as exc:
        require(diagnostic in str(exc), f"unexpected refusal: {exc!r}")
        return str(exc)
    raise ValueError(f"missing refusal: {diagnostic}")


def make_intent(name, section_radius, path_radius, density):
    circle = CircleGeometry(PlaneVector(0.0, 0.0), section_radius)
    arc = ArcGeometry(PlaneVector(0.0, path_radius), path_radius, -pi / 2, 0.0)
    return SweepIntent(name, circle, arc, density, SelfFileInput(join(LOCATOR, name + ".SLDPRT"), 1794000000))


def check_refusals(intent, candidate):
    wrong_part = SelfFileInput(join(LOCATOR, "DifferentPart.SLDPRT"), intent.OutputValue.SavedAt)
    detached_circle = CircleGeometry(PlaneVector(0.001, 0.0), intent.SectionValue.Radius)
    reversed_arc = ArcGeometry(intent.PathValue.Center, intent.PathValue.Radius, 0.0, -pi / 2)
    zero_path = ArcGeometry(intent.PathValue.Center, intent.SectionValue.Radius, -pi / 2, 0.0)
    refuses = {
        "mismatched_locator": expected_refusal(lambda: replace(intent, OutputValue=wrong_part), "must match"),
        "moved_section": expected_refusal(lambda: replace(intent, SectionValue=detached_circle), "origin centred"),
        "reversed_path": expected_refusal(lambda: replace(intent, PathValue=reversed_arc), "positive origin start"),
        "same_radii": expected_refusal(lambda: replace(intent, PathValue=zero_path), "separated measured radii"),
        "infinite_density": expected_refusal(lambda: replace(intent, DensityValue=float("inf")), "positive finite density"),
        "boolean_density": expected_refusal(lambda: replace(intent, DensityValue=True), "positive finite density"),
    }
    old = (candidate.ResolvedValue.RootsValue, None, 19000,
           candidate.ConfigValue.MapValue, candidate.ResolvedValue.ContextValue)
    refuses["unselected_sweep"] = expected_refusal(
        lambda: WriteResolMut(*old), "unsupported SOLIDWORKS body class moSweep_c schema 1", BodyUnsupported
    )
    refuses["warm_context"] = expected_refusal(
        lambda: WriteResolMut(*old[:-1], old[-1] | {"cmgr_f658": 1}, WriteSweeps=True),
        "unsupported cold SOLIDWORKS standard sweep context", BodyUnsupported,
    )
    data = candidate.FeatureValue.FieldsValue["f820"]
    data["f234"] = 1
    try:
        refuses["thin_sweep"] = expected_refusal(
            lambda: WriteResolMut(*old, WriteSweeps=True), "unsupported option", BodyUnsupported
        )
    finally:
        data["f234"] = 0
    return refuses


def run_worker(case, density, mode):
    section, path = dimensions(case, None if mode == "original" else mode)
    blocked = guard_runtime()
    intent = make_intent(case["name"], section, path, density)
    candidate = BuildSweepPart(intent)
    generated_again = BuildSweepPart(intent)
    require(candidate.BytesValue == generated_again.BytesValue, "same typed intent emitted different containers")
    check = inspect_output(candidate.BytesValue, candidate.StreamsValue, candidate.ConfigValue,
                           candidate.ResolvedValue, (section, path))
    check["refusals"] = check_refusals(intent, candidate)
    check["lengths"] = {key: len(value) for key, value in candidate.StreamsValue.items()}
    check["blocked_runtime_calls"] = len(blocked)
    require(not blocked, "SDK sweep attempted unapproved access")
    return check


def run_proof():
    density, cases = validate_spec(checked_json(HERE / "DisclosedSweepInputs.json", SPEC))
    native = checked_json(MEASURED, NATIVE)
    rows = []
    for case, witnessed in zip(cases, native["cases"], strict=True):
        original, section, path = (read_worker(case, density, mode) for mode in ("original", "section", "path"))
        require(witnessed["passed"] and original["candidate_sha256"] == witnessed["candidate_sha256"]["original"],
                "promoted typed writer differs from the native-tested original bytes")
        require(original["sketches"][0] == path["sketches"][0] and original["sketches"][1] == section["sketches"][1]
                and original["section_transport"]["transmit_sha256"] == path["section_transport"]["transmit_sha256"]
                != section["section_transport"]["transmit_sha256"],
                "one independent driver change disturbed the other owning sketch")
        require(len({row["candidate_sha256"] for row in (original, section, path)}) == 3
                and len({(row["lengths"]["Contents/Config-0-ResolvedFeatures"],
                          row["lengths"]["Contents/Config-0-GhostPartition"])
                         for row in (original, section, path)}) > 1,
                "independent input changes did not change linked serialized content and length")
        rows.extend({"name": case["name"], "state": mode, **row}
                    for mode, row in zip(("original", "section", "path"), (original, section, path), strict=True))
    prefix = ROOT / "src" / "convert" / "adapters" / "solidworks"
    scoped = (
        "Archive/Bodies/Layouts/Resolved/Sweeps", "Archive/Construction/Sweeps",
        "Archive/Partition/Sweeps", "Archive/Resolved/Sweeps", "Core/Preparation/Sweeps",
    )
    source_files = [path for folder in scoped for path in (prefix / folder).rglob("*.py")]
    source_files.extend(prefix / name for name in (
        "Archive/Bodies/WriteBodyMut.py", "Archive/Resolved/WriteResolMut.py",
        "Archive/Construction/Part/EmitPartArchive.py",
    ))
    return {
        "schema": "kit.sw2026.sdk-cold-standard-sweep.v1",
        "producer_base": "864c1da9f0eca3d5e217303dc1f696a3fb4b16a7",
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                          for path in sorted(source_files)},
        "observer_sha256": {name: sha256((HERE / name).read_bytes()).hexdigest()
                             for name in ("ProveSdkSweepPart.py", "AuditColdSweep.py", "SweepArchiveLayout.py",
                                          "SweepReplay.py", "SweepGhostGraph.py")},

        "disclosed_intents_sha256": SPEC, "disclosed_native_result_sha256": NATIVE,
        "native_processes_started": 0, "private_inputs_read": 0, "public_registration": False,
        "cases": rows, "measurements": 6,
    }


def read_worker(case, density, mode):
    request = json.dumps({"case": case, "density": density, "mode": mode}).encode()
    raw = check_output((sys.executable, "-I", "-B", str(__file__), "--worker"), input=request)
    return json.loads(raw)


def main():
    parser = ArgumentParser(description="prove fresh typed SDK sweep assembly and exact disclosed container parity")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    result = run_worker(**json.load(sys.stdin)) if args.worker else run_proof()
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
