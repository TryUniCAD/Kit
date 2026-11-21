from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
import json
import sys


TOOL = Path(__file__).resolve()
ROOT = TOOL.parents[4]
sys.path.insert(0, str(TOOL.parent))

from ProveColdPatternRead import datum_summary
from ProveLinearPatternModelRead import canon, digest, observe, pin, require


def worker():
    sys.path.insert(0, str(ROOT / "src"))
    from convert import open_document
    from interchange.serialization import dumps, loads

    raw = sys.stdin.buffer.read()

    def no_application(event, args):
        require(event not in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"),
                "typed datum projection attempted a vendor process")

    sys.addaudithook(no_application)
    document = open_document(raw, source_format="solidworks.sldprt", strict=True)
    plane = document.feature_timeline[-2]
    restored = loads(dumps(document))
    parents = {value.id: value.name for value in document.feature_timeline}
    details = datum_summary(restored, next(row for row in restored.feature_timeline if row.id == plane.id))
    require(datum_summary(document, plane) == details and not restored.validate(),
            "ordinary neutral JSON did not preserve the exact portable reference roles")
    require(details["angle_support"] == plane.name, "portable angled plane lost its actual named support")
    read = observe(raw, "read")
    result = {
        "plane": details,
        "actual_plane_inputs": [parents[key] for key in plane.input_feature_ids],
        "geometry_sha256": read["geometry_sha256"],
        "pattern": read["pattern"],
        "mode_without_geometry": observe(raw, "no-brep"),
        "mode_with_raw_geometry": observe(raw, "raw"),
    }
    print(canon(result).decode())


def measure(share, cold):
    from AuditSharedPatternWire import SOURCE_NAMES
    from ProveColdPatternRead import encode
    from ProveLocalPatternContainer import document_rows

    cold_bytes = cold.read_bytes()
    cold_cases = json.loads(cold_bytes)
    require(cold_cases["neutral_json_roundtrips"] == 6 and cold_cases["exact_generated_hashes_required"],
            "cold proof omitted normal portable JSON or exact source custody")
    prior = ROOT / "re/solidworks/measurements/2026/SdkWarmAngularPatternRead01.json"
    expected = json.loads(prior.read_bytes())["cases"]
    cases = {}
    for path, sha, _ in document_rows(share):
        if path.name not in SOURCE_NAMES:
            continue
        raw = pin(path, sha)
        outcome = run([sys.executable, "-I", "-B", str(TOOL), "--worker"],
                      input=raw, capture_output=True, check=False, timeout=60, cwd=ROOT)
        require(outcome.returncode == 0 and not outcome.stderr, outcome.stderr.decode())
        result = json.loads(outcome.stdout)
        original = expected[path.name]
        original_pattern, current_pattern = original["pattern"], result["pattern"]
        if original_pattern is not None:
            require(current_pattern is not None, "portable datum lost the previously qualified pattern")
            fields = set(original_pattern) - {"write_refusal"}
            require(all(current_pattern[key] == original_pattern[key] for key in fields)
                    and current_pattern["write_refusal"].startswith("native-only feature definitions"),
                    "portable datum altered active pattern semantics or admitted writing")
        else:
            require(current_pattern is None, "portable datum admitted the overhanging topology")
        require(result["geometry_sha256"] == original["geometry_sha256"],
                "portable datum projection altered the original saved solid")
        require(result["actual_plane_inputs"] == original["datum"]["plane_inputs"],
                "stored angular support and hinge dependencies changed")
        cases[path.name] = {
            "source_sha256": sha,
            "geometry_sha256": result["geometry_sha256"],
            "native_geometry_unchanged": True,
            "preserved_generic_overhang": result["pattern"] is None,
            "datum": result["plane"],
            "source_parent_names": result["actual_plane_inputs"],
            "no_geometry_document_sha256": result["mode_without_geometry"]["document_sha256"],
            "raw_document_sha256": result["mode_with_raw_geometry"]["document_sha256"],
        }
    require(set(cases) == SOURCE_NAMES, "incomplete warm cohort")
    record = {
        "schema": "kit.sw2026.portable-oblique-pattern-datums.v1",
        "build": "34.5.2.0604",
        "guarded_warm_processes": len(cases),
        "exact_cold_readback_receipt_sha256": digest(cold_bytes),
        "prior_warm_receipt_sha256": digest(prior.read_bytes()),
        "warm": cases,
        "cold": cold_cases,
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
    }
    return encode(record)


def main():
    parser = ArgumentParser()
    parser.add_argument("--share", type=Path)
    parser.add_argument("--cold", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    payload = measure(args.share, args.cold)
    with args.output.open("xb") as output:
        output.write(payload)
    print(digest(payload))


if __name__ == "__main__":
    main()
