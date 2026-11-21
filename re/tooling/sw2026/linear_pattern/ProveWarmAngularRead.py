from argparse import ArgumentParser
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
BASE = "bfac46e67751493f1f25c7453b7e8f09d0c30234"
sys.path.insert(0, str(TOOL.parent))
from ProveLinearPatternModelRead import CONTROL_ROWS, canon, digest, observe, pin, require


def fractures(raw):
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatOwner import ReadPatOwner
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    good = ReadPatOwner(link, header)
    tilt = good.DatumValue.TiltValue
    plane = good.DatumValue.PlaneValue.FieldsValue["f6f8"].FieldsValue
    interface = plane["f88"].FieldsValue
    hinge = tilt.HingeValue.FieldsValue["f700"].FieldsValue
    reference = hinge["f88"].FieldsValue["f58"].FieldsValue["ff0"]
    checks = (
        (plane, "f148", 3, "unreversed live driver"),
        (interface, "f10", interface["f18"], "unreversed live driver"),
        (tilt.DriverValue.FieldsValue, "f58", tilt.AngleValue / 2, "unreversed live driver"),
        (reference, "f08", reference["f08"] + 1, "registered creation"),
        (plane, "b3", plane["b3"] - .001, "finite hinge"),
        (good.DatumValue.LineValue.FieldsValue, "fc8", {"x": .1, "y": .2, "z": .3}, "plane border or signed normal"),
    )
    results = []
    for fields, key, new, expected in checks:
        original = fields[key]
        fields[key] = new
        try:
            ReadPatOwner(link, header)
        except ValueError as error:
            require(expected in str(error), "contradicted owner reached the wrong refusal")
            results.append({"field": key, "refusal": str(error)})
        else:
            raise ValueError("contradicted angular owner passed")
        finally:
            fields[key] = original
    require(ReadPatOwner(link, header) == good, "negative case altered the next accepted result")
    return results


def worker(source, mode):
    sys.path.insert(0, str(source))
    raw = sys.stdin.buffer.read()

    def deny_launch(event, args):
        require(event not in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"),
                "unexpected external process in SDK read")

    sys.addaudithook(deny_launch)
    if mode == "bad":
        output = fractures(raw)
    elif mode == "cold":
        from convert import open_document
        try:
            open_document(raw, source_format="solidworks.sldprt", strict=True)
        except ValueError as error:
            require("no readable Parasolid payload" in str(error), "cold refusal changed")
            output = {"strict_refusal": str(error), "without_brep": observe(raw, "no-brep")}
        else:
            raise ValueError("unqualified cold geometry entered the strict reader")
    else:
        from convert import open_document
        from interchange.serialization import to_data

        output = {name: observe(raw, name) for name in ("read", "no-brep", "raw")}
        if mode == "tilt":
            doc = open_document(raw, source_format="solidworks.sldprt", strict=True)
            names = {row.id: row.name for row in doc.feature_timeline}
            axis, plane, _ = doc.feature_timeline[-3:]
            angle, = [row for row in doc.parameters if row.owner_id == plane.id]
            output["datum"] = {
                "hinge_inputs": [names[identity] for identity in axis.input_feature_ids],
                "plane_inputs": [names[identity] for identity in plane.input_feature_ids],
                "hinge_name": axis.name, "angle": angle.value.value, "unit": angle.value.unit, "kind": angle.value.kind.value,
                "dimension_id": angle.attributes.get("typed_archive_owner", {}).get("dimension_id"),
                "pre_datum_features_sha256": digest(canon(to_data(doc.feature_timeline[:-3]))),
                "physical_faces": len(doc.brep.faces),
            }
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "SDK reader loaded a CAD dependency")
    print(canon(output).decode())


def request(source, mode, raw):
    result = run([sys.executable, "-I", "-B", str(TOOL), "--source", str(source), "--worker", mode],
                 input=raw, capture_output=True, check=False, timeout=45)
    require(result.returncode == 0, result.stderr.decode())
    return json.loads(result.stdout)


def source_observation(share, path, sha):
    from AuditSharedPatternWire import SOURCE_NAMES

    for name, top, root in (
        ("LocalLinearPatternDatumPlacement01", "LinearPatternEnvelope02", "DisclosedTrial"),
        ("LocalLinearPatternDatumHeightNative01", "LinearPatternDatumHeight01", "DisclosedHeights"),
    ):
        directory = share / top / root
        if path.name not in SOURCE_NAMES or directory not in path.parents:
            continue
        receipt = json.loads((ROOT / "re/solidworks/measurements/2026" / (name + ".json")).read_bytes())
        native = json.loads(pin(directory / "Result.json", receipt["native_result_sha256"]))
        stage = "spacing-reopen" if path.name == "DirectionEnvelopeSpacing.SLDPRT" else "pristine-reopen"
        matches = [row for row in native["phases"] if row["phase"] == stage
                   and ("case" not in row or row["case"] == path.parent.name)]
        row, = matches
        proof = json.loads(pin(path.parent / stage / "Record.json", row["sha256"]))
        require(row["passed"] and proof["passed"] and proof["artifact"]["sha256"] == sha,
                "scoped saved model differs from the independently reopened native state")
        return row["sha256"], proof["reopened"]
    raise ValueError("unsupported source oracle custody")


def compare(before, after, native, overhang):
    basis = before["datum"]
    datum = after["datum"]
    constraints = native["datum"]["constraints"]
    require(basis["unit"] == "mm" and datum["kind"] == "angle" and datum["unit"] == "rad"
            and datum["angle"] == constraints[0]["angle_or_distance"]
            and datum["dimension_id"] is not None
            and datum["hinge_inputs"] == [row["name"] for row in native["datum"]["hinge"]["parents"]]
            and datum["plane_inputs"] == [datum["hinge_inputs"][1], datum["hinge_name"]]
            and datum["pre_datum_features_sha256"] == basis["pre_datum_features_sha256"]
            and datum["physical_faces"] == native["bounds"]["faces"],
            "saved angle or dependency owners differ from native evidence")
    keys = ("geometry_sha256", "payload_sha256", "design_ids", "brep_ids", "feature_ids", "final_feature_ids", "sketches_and_planes_sha256")
    require(all(before["read"][key] == after["read"][key] for key in keys)
            and before["raw"] == after["raw"] and before["no-brep"] == after["no-brep"],
            "rebound saved geometry or the unchanged reader routes differ")
    pat = after["read"]["pattern"]
    if overhang:
        require(pat is None and datum["physical_faces"] == 17, "overhanging pattern escaped the body scope")
    else:
        values = native["pattern"]["values"]
        mass = native["mass"]
        require(before["read"]["pattern"] is None and pat["parents"] == native["pattern"]["parents"]
                and pat["signed_direction"] == native["datum"]["signed_normal"]
                and pat["count"] == values["D1TotalInstances"] and pat["spacing_mm"] == values["D1Spacing"] * 1000.0
                and pat["face_count"] == datum["physical_faces"]
                and pat["atom_lineage"] == [101, 102, 103]
                and isclose(pat["volume_mm3"] / 1e9, mass["volume"], rel_tol=1e-12)
                and all(isclose(found / 1000, expected, rel_tol=1e-12) for found, expected in zip(pat["centroid_mm"], mass["com"], strict=True)),
                "typed saved pattern differs from actual geometry or native driving ownership")


def measure(share, candidates):
    from AuditSharedPatternWire import SOURCE_NAMES
    from ProveLocalPatternContainer import document_rows

    with TemporaryDirectory(prefix="KitWarmAngularBase.") as tmp:
        data = check_output(["git", "archive", BASE, "src"], cwd=ROOT)
        with tarfile.open(fileobj=BytesIO(data), mode="r:") as source:
            source.extractall(tmp, filter="data")
        base, current = Path(tmp) / "src", ROOT / "src"
        positives, controls, faults = {}, {}, None
        for path, sha, _ in document_rows(share):
            raw = pin(path, sha)
            mode = "tilt" if path.name in SOURCE_NAMES else "read"
            a, b = request(base, mode, raw), request(current, mode, raw)
            if mode == "tilt":
                observation, native = source_observation(share, path, sha)
                compare(a, b, native, path.name == "DirectionEnvelopeSpacing.SLDPRT")
                positives[path.name] = {"native_source_sha256": sha, "native_observation_sha256": observation,
                                        "datum": b["datum"], "pattern": b["read"]["pattern"],
                                        "geometry_sha256": b["read"]["geometry_sha256"]}
                if faults is None:
                    faults = request(current, "bad", raw)
            else:
                require(a == b, "earlier principal pattern read changed")
                controls[path.name] = {"source_sha256": sha, "document_sha256": b["read"]["document_sha256"]}
        for name, sha in CONTROL_ROWS:
            path = ROOT / "re/solidworks/v2026/corpus" / name
            raw = pin(path, sha)
            a, b = request(base, "read", raw), request(current, "read", raw)
            require(a == b, "earlier ordinary part reader changed")
            controls[path.name] = {"source_sha256": sha, "document_sha256": b["read"]["document_sha256"]}
        wire = ROOT / "re/solidworks/measurements/2026/SharedAngularPatternWire01.json"
        for row in json.loads(wire.read_bytes())["generated"]:
            name, sha = row["name"], row["sha256"]
            raw = pin(candidates / name, sha)
            a, b = request(base, "cold", raw), request(current, "cold", raw)
            require(a == b, "cache-free or metadata-only route changed")
            controls[name] = {"source_sha256": sha, **b}
    require(len(positives) == 4 and len(controls) == 10 and len(faults) == 6, "measured matrix incomplete")
    files = sorted((ROOT / "src/convert/adapters/solidworks/Core/TypedResolved/Patterns").glob("*.py"))
    return {"schema": "kit.sw2026.warm-angular-pattern-read.v1", "build": "34.5.2.0604", "sdk_baseline": BASE,
            "cases": positives, "unchanged_controls": controls, "owner_refusals": faults, "guarded_processes": 29,
            "codec_sha256": {file.name: digest(file.read_bytes()) for file in files},
            "native_processes_started": 0, "heldout_inputs_read": 0, "native_files_published": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--share", type=Path)
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--worker", choices=("read", "tilt", "bad", "cold"))
    args = parser.parse_args()
    if args.worker:
        worker(args.source, args.worker)
        return
    payload = json.dumps(measure(args.share, args.candidates), sort_keys=True, indent=2, allow_nan=False).encode() + b"\n"
    with args.output.open("xb") as stream:
        stream.write(payload)
    print(digest(payload))


if __name__ == "__main__":
    main()
