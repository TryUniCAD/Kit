from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from subprocess import run
import json
import os
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src")]

from SdkNativeRoundTrips import roundtrips
from convert.adapters.solidworks.Archive.Construction.Geometry.MakePlaneFrame import MakePlaneFrame
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import PrepareNestedAssembly
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument, ComponentDoc
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.serialization.Deserialize import FromData


CASES = {
    "SdkNestedAssemblyNative01": "4fc7cc504ab20b275abc41d13832adcaa9c0ce0e9da999fb3fb898e9359ec40a",
    "SdkRepeatedNestedAssemblyNative01": "b0deabf21fd6701b11f3c8e77023235e29c1895a7e08da1802c7cae96de9a4e4",
}


def digest(raw):
    return sha256(raw).hexdigest()


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def checked(path, expected):
    raw = path.read_bytes()
    require(digest(raw) == expected and not path.is_symlink(), f"disclosed nested identity differs: {path.name}")
    return raw


def authored_document(request):
    definitions = []
    parts = []
    occurrences = []
    configs = {}
    root = request["root"]
    source_rows = request["definitions"]
    root_settings = next(row["request"] for row in source_rows if row["id"] == root)
    root_planes = root_settings["system"]["planes"]
    for row in source_rows:
        identity, kind, settings = row["id"], row["kind"], row["request"]
        if kind == "part":
            part = FromData(settings["document"])
            document_id = "doc:" + identity
            parts.append(ComponentDoc(document_id, part))
            selected, = part.configurations
            definition = ComponentDef(identity, part.metadata["name"], kind, document_id=document_id,
                                      configuration_id=selected.id, configuration_name=selected.name,
                                      body_ids=tuple(body.id for body in part.bodies))
        else:
            require(kind == "assembly" and settings["system"]["planes"] == root_planes, "unexpected disclosed assembly datums")
            selected = Configuration("cfg:" + identity, settings["configuration_name"], active=True)
            definition = ComponentDef(identity, settings["name"], kind,
                                      configuration_id=selected.id, configuration_name=selected.name)
        configs[identity] = selected
        definitions.append(definition)
    for row in source_rows:
        owner = row["id"]
        for index, pair in enumerate(row.get("occurrences", ())):
            value, target = pair["occurrence"], pair["target"]
            frame = MakePlaneFrame(tuple(value["origin"]), tuple(value["u"]), tuple(value["v"]))
            pose = tuple(component for axis in range(3) for component in (
                frame.AxisU[axis], frame.AxisV[axis], frame.NormalValue[axis], 1000 * frame.OriginValue[axis])) + (0, 0, 0, 1)
            selected = configs[target]
            occurrences.append(ComponentInst(f"inst:{owner}:{index}", value["name"], target, owner,
                                             TransformMatrix(pose), order=index,
                                             configuration_name=selected.name, configuration_id=selected.id))
    planes = tuple(SupportPlane("plane:" + axis, name, Transform(*(SpaceVector(*vector) for vector in
                   (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue))))
                   for axis, name in root_planes.items() for frame in (PrincipalFrame(axis),))
    doc = CadDocument(CadSource("neutral", "authored nested model", ""), (configs[root],), (), planes, (), (), (), (),
                      metadata={"name": root_settings["name"]},
                      assembly=AssemblyData(root, tuple(definitions), tuple(occurrences), tuple(parts)))
    return doc, root_settings["output"]


def worker(payload):
    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    doc, target = authored_document(payload["request"])
    doc.assert_valid()
    blocked = []

    def forbid(event, _arguments):
        if event in ("open", "os.listdir", "os.scandir", "os.exec", "os.system", "os.posix_spawn", "ctypes.dlopen") or event.startswith(("socket.", "subprocess.")):
            blocked.append(event)
            raise ValueError(f"nested assembly writer tried to access an external file or program: {event}")

    sys.addaudithook(forbid)
    outputs = PrepareNestedAssembly(doc, target["path_name"], target["saved_at"])
    rows = {}
    for path, value in outputs:
        name = path.name
        parent = path.suffix.casefold() == ".sldasm"
        archive = SldprtArchive.from_bytes(value.BytesValue)
        link, mates, _, _, streams = roundtrips(archive, parent)
        require((mates is not None) == parent and (not parent or not mates.RootsValue),
                "rigid plain nested composition changed the mate inventory")
        require(len(value.ReferenceValues) == len(value.ChildTargets), "unowned nested reference")
        rows[name] = {"sha256": digest(value.BytesValue), "bytes": len(value.BytesValue), "activity": value.ActivityValue,
                      "native_path": str(path), "streams": streams, "references": len(value.ReferenceValues),
                      "map_next": link.ResolvedValue.MapValue.CounterValue}
    require(not blocked and not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                                   for name in sys.modules), "nested assembly used runtime file data or a CAD process")
    file = PureWindowsPath(target["path_name"]).name
    return {"root": file, "worker_pid": os.getpid(), "runtime_file_reads": 0, "outputs": rows,
            "definition_count": len(outputs), "root_activity": rows[file]["activity"], "passed": True}


def audit(workspace):
    results = {}
    for name, pin in CASES.items():
        capsule = workspace / name
        fixture = json.loads(checked(capsule / "Fixture.json", pin))
        request = json.loads(checked(capsule / "NeutralRequest.json", fixture["request_sha256"]))
        trial = json.loads(checked(capsule / "Prediction.json", fixture["prediction_sha256"]))
        outcomes = []
        for _ in range(2):
            result = run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                         input=json.dumps({"request": request}), capture_output=True, text=True, timeout=120)
            require(result.returncode == 0 and not result.stderr, result.stderr[-2600:])
            outcomes.append(json.loads(result.stdout))
        first, second = outcomes
        require(first.pop("worker_pid") != second.pop("worker_pid") and first == second,
                "two fresh workers did not reproduce the same nested bundle")
        require(first["definition_count"] == len(trial["definitions"]) and first["root_activity"] == len(trial["initial"]["occurrences"]),
                "generated definition or occurrence closure differs from the independent prediction")
        baseline = {}
        for row in fixture["files"].values():
            file = row["file"]
            before = SldprtArchive.from_bytes(checked(capsule / "FrozenGenerated" / file, row["sha256"]))
            after = first["outputs"][file]
            unchanged = [record.name for record in before.records if record.name in after["streams"]
                         and after["streams"][record.name]["sha256"] == digest(record.data)]
            baseline[file] = {"exact_container": row["sha256"] == after["sha256"], "exact_streams": sorted(unchanged)}
        results[name] = {**first, "prior_fixture_sha256": pin, "prior_native_candidate_comparison": baseline}
    return {"schema": "kit.sw2026.neutral-nested-assembly-composition.v1", "cases": results, "fresh_processes": 4,
            "native_processes_started": 0, "heldout_inputs_read": 0, "public_writer": False, "passed": True}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        blob = (json.dumps(audit(args.workspace), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as output:
            output.write(blob)
        print(digest(blob))
