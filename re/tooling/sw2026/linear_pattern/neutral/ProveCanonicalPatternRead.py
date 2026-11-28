from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
FIXTURE = "5784abcd6ccc6e93feb88463333b5668bf4fd12f18fa2bde5efbfcc1ccabcdef"
DEFAULTS = "ef52c12bc4a22a0de666b043ad586871a0bdfa03e877ac62e591b40dfbaa2df7"
FORMAT = "solidworks.sldprt"
GATE = ("src/convert/adapters/solidworks/Core/TypedResolved/Patterns/Cold/"
        "CheckPatViews.py")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encode(data):
    return (json.dumps(data, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def locked(path, sha):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == sha, "unverified fixture: " + path.name)
    return json.loads(raw)


def denied(data):
    from convert import open_document
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat

    try:
        open_document(BytesIO(data), source_format=FORMAT, strict=True)
    except SldprtFormat as error:
        require(str(error) == "SLDPRT contains no readable Parasolid payload", str(error))
        return
    raise ValueError("unqualified annotation recovered provisional native geometry")


def invalid(plan, outcome):
    from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import IdentityXform
    from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
    from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph

    graph = MakePatGraph(plan)
    body = graph.StockValue.SystemValue.RootValue.FieldsValue
    catalog = body["fa48"].FieldsValue
    top, back = (row["o"].FieldsValue for row in catalog["items"])
    if outcome == "unknown-name":
        top["f358"] = "*Bottom"
    elif outcome == "wrong-order":
        catalog["items"] = tuple(reversed(catalog["items"]))
    elif outcome == "wrong-top-frame":
        top["f368"] = IdentityXform()
    elif outcome == "wrong-back-origin":
        back["f368"]["f58"] = 0.001
    elif outcome == "wrong-top-id":
        top["f360"] += 2
    elif outcome == "wrong-frontier":
        body["feb0"] = top["f360"]
    else:
        raise ValueError("unknown test contrast")
    return EmitPatArchive(graph)[1]


def worker(folder):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parents[1])]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
    from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph
    from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import PlanLinPattern
    from interchange import CadDocument
    from ProveColdPatternRead import summary

    job = json.load(sys.stdin)
    document = CadDocument.from_json(encode(job["document"]).decode())
    plan = PlanLinPattern(document, SelfFileInput(**job["target"]))
    streams, data = EmitPatArchive(MakePatGraph(plan))
    path = folder / "Canonical.SLDPRT"
    path.write_bytes(data)
    negatives = {label: invalid(plan, label) for label in (
        "unknown-name", "wrong-order", "wrong-top-frame", "wrong-back-origin", "wrong-top-id", "wrong-frontier",
    )}

    def audit(name, args):
        require(name not in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"),
                "strict read launched an external application")

    sys.addaudithook(audit)
    result = summary(open_document(BytesIO(data), source_format=FORMAT, strict=True))
    require(summary(open_document(path, strict=True)) == result, "strict path and stream disagree")
    step = document.feature_timeline[-1].definition
    require((result["count"], result["pitch_mm"], result["reversed"], result["face_count"]) == (
        step.instance_count, step.spacing.value * 1000, step.reversed, document.bodies[0].topology.face_count,
    ), "read geometry lost original pattern controls")
    for label, raw in negatives.items():
        require(raw != data, "negative did not change archive: " + label)
        denied(raw)
    return {"bytes": len(data), "sha256": sha256(data).hexdigest(), "streams": len(streams),
            "count": result["count"], "pitch_mm": result["pitch_mm"], "reversed": result["reversed"],
            "faces": result["face_count"], "strict_path_reads": 1, "strict_stream_reads": 1,
            "refusals": sorted(negatives)}


def measure(fixture):
    jobs = locked(fixture, FIXTURE)
    previous = locked(ROOT / "re/solidworks/measurements/2026/SharedLinearPatternDefaults01.json", DEFAULTS)
    results = {}
    with TemporaryDirectory(prefix="KitCanonicalPatternRead.") as temp:
        for name, job in sorted(jobs.items()):
            folder = Path(temp) / name
            folder.mkdir()
            process = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(folder)),
                          input=encode(job), capture_output=True, timeout=60, check=False)
            require(process.returncode == 0 and not process.stderr, process.stderr.decode())
            row = json.loads(process.stdout)
            expected = previous["cases"][name]
            require((row["bytes"], row["sha256"]) == (expected["complete_bytes"], expected["complete_file_sha256"]),
                    "canonical bytes differ from frozen generation")
            results[name] = row
    return {"schema": "kit.sw2026.canonical-cold-pattern-reader.v1", "source_fixture_sha256": FIXTURE,
            "canonical_authority_sha256": DEFAULTS, "native_processes_started": 0,
            "reader_gate_sha256": sha256((ROOT / GATE).read_bytes()).hexdigest(),
            "proof_sha256": sha256(HERE.read_bytes()).hexdigest(), "cases": results}


def main():
    parser = ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker is not None:
        sys.stdout.buffer.write(encode(worker(args.worker)))
    else:
        if args.fixture is None or args.output is None:
            parser.error("--fixture and --output are required")
        result = measure(args.fixture)
        with args.output.open("xb") as output:
            output.write(encode(result))


if __name__ == "__main__":
    main()
