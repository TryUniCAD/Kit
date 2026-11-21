from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from math import isclose
from pathlib import Path
from subprocess import check_output, run
from tempfile import TemporaryDirectory
import json
import sys
import tarfile


TOOL = Path(__file__).resolve()
ROOT = TOOL.parents[4]
BASE = "21ac76977b4f043b7e073b269de7a73fe70617f3"
LOCK = "8239fc92779aadd6a0116ad2df9e7969568394a301e1ed11aa44fc3875ac0426"
ARCHIVE_PROOF = "85b4255dc79af7ea847b117fd5353bbf6dac7741177a77667efb2069e3883012"
KIND = "solidworks.sldprt"
CONTROL_ROWS = (
    ("ladder/L1_boss.SLDPRT", "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"),
    ("principal-revolve-discovery/PrincipalRevolveTopForward.SLDPRT", "4bf2c202be9ae4fc7786e50a92c4f83dc17ea4bc80492b7173075d74f678d3f0"),
)
NATIVE_PHASES = ("pristine-reopen", "spacing-reopen", "instances-reopen")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def pin(path, sha, count=None):
    require(path.is_file() and not path.is_symlink(), "missing disclosed file")
    raw = path.read_bytes()
    require(digest(raw) == sha and (count is None or len(raw) == count), "disclosed bytes differ")
    return raw


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def observe(raw, mode):
    from convert import open_document, registry, write_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.registry.RegistryErrors import RegistryError
    from interchange.Features.FeatureKinds import LinearPattern
    from interchange.serialization import to_data

    if mode == "raw":
        doc = registry.read(raw, format_id=KIND, options=ReadOptions(extract_raw_brep=True))
    else:
        doc = open_document(raw, source_format=KIND, include_brep=mode != "no-brep", strict=True)
    require(not doc.validate(), "public reader returned invalid neutral model")
    brep = doc.brep
    model = None if brep is None else replace(
        brep, bodies=tuple(replace(value, design_body_id="") for value in brep.bodies)
    )
    dissolved = {
        "document_sha256": digest(canon(to_data(doc))),
        "geometry_sha256": None if model is None else digest(canon(to_data(model))),
        "payload_sha256": [value.sha256 for value in doc.brep_payloads],
        "feature_ids": [value.id for value in doc.feature_timeline],
        "general_features_sha256": digest(canon(to_data(doc.feature_timeline[:-1]))),
        "sketches_and_planes_sha256": digest(canon(to_data((doc.sketches, doc.support_planes)))),
        "design_ids": [value.id for value in doc.bodies],
        "final_feature_ids": [value.final_feature_id for value in doc.bodies],
        "brep_ids": [] if brep is None else [value.id for value in brep.bodies],
        "pattern": None,
    }
    step = doc.feature_timeline[-1]
    if not isinstance(step.definition, LinearPattern):
        dissolved["last_type"] = None if step.definition is None else type(step.definition).__name__
        return dissolved
    definition = step.definition
    by_id = {value.id: value for value in doc.parameters}
    params = [by_id[value] for value in step.parameter_ids]
    by_selection = {value.id: value for value in doc.selections}
    selection = by_selection[definition.direction_selection_id]
    (element,) = selection.path
    require(element.entity_kind == "support_plane" and not element.subelement and selection.point is None
            and step.selection_ids == (selection.id,) and not any(":edge:" in value.id and value.id.startswith("sldprt:selection:47:")
                                                               for value in doc.selections),
            "pattern kept a guessed edge or line-point selection")
    plane = next(value for value in doc.support_planes if value.id == element.entity_id)
    axis = plane.transform.z_axis
    sign = -1 if definition.reversed else 1
    body, = doc.bodies
    kernel, = brep.bodies
    proof = doc.metadata["solidworks.typed_linear_pattern"]
    require(kernel.design_body_id == body.id and proof["public_writer_qualified"] is False, "physical or writer scope changed")
    writer = registry.GetWriter(KIND)
    require(not writer.supports(doc, Path("UnusedPattern.SLDPRT")), "pattern entered the public writer")
    output = BytesIO(b"unchanged destination")
    try:
        write_document(doc, output, destination_format=KIND, allow_carrier=False, overwrite=True)
    except (ValueError, RegistryError) as error:
        write_refusal = str(error)
    else:
        raise ValueError("unsupported native pattern emitted through the public writer")
    require(output.getvalue() == b"unchanged destination", "refused writer changed the stream")
    dissolved["pattern"] = {
        "count": definition.instance_count, "spacing_mm": definition.spacing.value,
        "selected_path": (element.entity_kind, element.entity_id), "plane": plane.name,
        "signed_direction": tuple(sign * value for value in (axis.x, axis.y, axis.z)),
        "parents": [next(value.name for value in doc.feature_timeline if value.id == identity) for identity in step.input_feature_ids],
        "drivers": {value.name: {"id": value.id, "value": value.value.value,
                                "unit": value.value.unit, "role": value.role.value,
                                "owner": dict(value.attributes["typed_archive_owner"])} for value in params},
        "parameter_ids": step.parameter_ids,
        "physical_body_node": proof["physical_body_node"], "atom_lineage": proof["native_atom_lineage"],
        "face_count": body.topology.face_count, "body_name": body.name,
        "volume_mm3": body.topology.volume, "centroid_mm": body.attributes["solidworks.body_centroid_mm"],
        "dormant_drivers": proof["driver_roles"][2:], "write_refusal": write_refusal,
    }
    return dissolved


def refusals(raw):
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatOwner import ReadPatOwner
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    plate, _, seed, pattern = link.ResolvedValue.RootsValue[-4:]
    fields = pattern.FieldsValue
    line = fields["f1288"].FieldsValue
    datum = line["f58"].FieldsValue
    chooser = fields["f548"]["items"][0]["o"].FieldsValue
    originals = ReadPatOwner(link, header)
    cases = (
        (fields, "f1258", fields["f1268"], "separate actual count and pitch"),
        (fields, "f1290", fields["f1288"], "unsupported saved linear pattern mode"),
        (datum["ff0"], "f08", datum["ff0"]["f08"] + 1, "actual local datum and reversal"),
        (chooser, "ff0", seed.FieldsValue["f548"]["items"][0]["o"].FieldsValue["ff0"], "alternate surface representations"),
        (fields["f530"]["items"][0], "o", plate.FieldsValue["f528"]["items"][0]["o"], "actual joined seed and plate"),
        (fields["fa50"], "f20", 1.0, "alternate original dimension record"),
    )
    rows = []
    for owner, key, replacement, message in cases:
        original = owner[key]
        owner[key] = replacement
        try:
            ReadPatOwner(link, header)
        except ValueError as error:
            require(message in str(error), "invalid source hit an unrelated refusal")
            rows.append({"field": key, "refusal": str(error)})
        else:
            raise ValueError("unsafe typed pattern owner passed")
        finally:
            owner[key] = original
    point = line["fc8"]
    line["fc8"] = {"x": 9.0, "y": -8.0, "z": 7.0}
    require(ReadPatOwner(link, header) == originals, "unresolved cached point entered read semantics")
    line["fc8"] = point
    return {"refusals": rows, "fc8_point_independent": True}


def worker(source, mode):
    sys.path.insert(0, str(source))
    raw = sys.stdin.buffer.read()

    def deny_launch(event, args):
        require(event not in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"),
                "unexpected external process in SDK read")

    sys.addaudithook(deny_launch)
    result = refusals(raw) if mode == "bad" else observe(raw, mode)
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                    for name in sys.modules), "SDK reader loaded a CAD dependency")
    print(canon(result).decode())


def call_worker(src, mode, raw):
    result = run((sys.executable, "-I", "-B", str(TOOL), "--worker", mode, "--source", str(src)),
                 input=raw, capture_output=True, check=False, timeout=40)
    require(result.returncode == 0, result.stderr.decode(errors="replace"))
    return json.loads(result.stdout)


def compare_sample(raw, observed, base):
    prior = call_worker(base, "read", raw)
    result = call_worker(ROOT / "src", "read", raw)
    pattern = result["pattern"]
    require(prior["pattern"] is None and pattern is not None, "wrong version of normal public pattern path")
    keys = ("geometry_sha256", "payload_sha256", "design_ids", "brep_ids", "feature_ids", "final_feature_ids",
            "general_features_sha256", "sketches_and_planes_sha256")
    require(all(prior[key] == result[key] for key in keys), "normal body geometry IDs, tree, profiles or payloads changed")
    values = observed["pattern"]["values"]
    require(pattern["count"] == values["D1TotalInstances"]
            and pattern["spacing_mm"] == values["D1Spacing"] * 1000.0
            and pattern["drivers"]["D1"]["value"] == pattern["count"]
            and pattern["drivers"]["D3"]["value"] == pattern["spacing_mm"]
            and pattern["drivers"]["D1"]["owner"]["slot"] == "f1258"
            and pattern["drivers"]["D3"]["owner"]["slot"] == "f1260"
            and all(value["role"] == "driving" for value in pattern["drivers"].values())
            and pattern["parents"] == observed["pattern"]["parents"]
            and pattern["signed_direction"] == observed["direction"]["signed_direction_sketch"]
            and pattern["face_count"] == observed["bounds"]["faces"]
            and pattern["body_name"] == observed["tree"][-1]["name"]
            and isclose(pattern["volume_mm3"] / 1e9, observed["mass"]["volume"], rel_tol=1e-12)
            and all(isclose(value / 1000, target, rel_tol=1e-12, abs_tol=1e-12)
                    for value, target in zip(pattern["centroid_mm"], observed["mass"]["com"], strict=True)),
            "neutral pattern count pitch direction identity or saved mass differs from the native record")
    for mode in ("no-brep", "raw"):
        require(call_worker(ROOT / "src", mode, raw) == call_worker(base, mode, raw),
                "existing excluded reader route changed")
    return result


def measure(packet, output):
    require(packet.name == "LinearPatternSourcePacket03", "use the disclosed pattern packet only")
    check_output(("git", "merge-base", "--is-ancestor", BASE, "HEAD"), cwd=ROOT)
    proof = ROOT / "re/solidworks/measurements/2026/LocalLinearPatternTypedArchive01.json"
    pin(proof, ARCHIVE_PROOF)
    lock = json.loads(pin(packet / "Progress/disclosed-lock.json", LOCK))
    require(lock["cohort"] == "disclosed" and lock["passed"] and lock["distinct_processes"] == 14
            and tuple(case["name"] for case in lock["cases"]) == ("D01X", "D02Y"), "disclosed custody differs")
    paths = sorted((ROOT / "src/convert/adapters/solidworks/Core/TypedResolved/Patterns").glob("*.py"))
    paths += [ROOT / "src/convert/adapters/solidworks/Core/Adapter.py", TOOL]
    with TemporaryDirectory(prefix="KitPatternBaselines-") as temp:
        stage = Path(temp)
        source_archive = check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with tarfile.open(fileobj=BytesIO(source_archive), mode="r:") as stream:
            stream.extractall(stage, filter="data")
        base = stage / "src"
        cases, faults = {}, None
        for case in lock["cases"]:
            area = packet / "DisclosedNative" / case["name"]
            phases = {row["phase"]: row for row in case["phases"]}
            for pinned, phase in zip(case["native_sources"], NATIVE_PHASES, strict=True):
                raw = pin(area / pinned["name"], pinned["sha256"], pinned["bytes"])
                report = json.loads(pin(area / phase / "Record.json", phases[phase]["record_sha256"]))
                require(report["native_sha256"] == pinned["sha256"] and report["open"] == {"opened": True, "errors": 0, "warnings": 0},
                        "independent source observation changed")
                cases[pinned["name"]] = compare_sample(raw, report["reopened"], base)
                if faults is None:
                    faults = call_worker(ROOT / "src", "bad", raw)
        controls = {}
        for filename, expected in CONTROL_ROWS:
            raw = pin(ROOT / "re/solidworks/v2026/corpus" / filename, expected)
            old = call_worker(base, "read", raw)
            require(old == call_worker(ROOT / "src", "read", raw), "established ordinary reader changed")
            controls[filename] = old["document_sha256"]
    result = {"schema": "kit.sw2026.linear-pattern-model-read.v1", "before_revision": BASE,
              "archive_receipt_sha256": ARCHIVE_PROOF, "disclosed_lock_sha256": LOCK,
              "implementation_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in paths},
              "worker_processes": 6 * len(cases) + 2 * len(controls) + 1, "native_processes_started": 0,
              "heldout_inputs_read": 0, "native_outputs_written": 0, "cases": cases, "malformed": faults,
              "unchanged_controls": controls, "unchanged_nonprojecting_modes": ["no-brep", "raw"]}
    encoded = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"cases": len(cases), "worker_processes": result["worker_processes"], "sha256": digest(encoded)}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("read", "no-brep", "raw", "bad"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker is None:
        measure(args.packet, args.output)
    else:
        worker(args.source, args.worker)
