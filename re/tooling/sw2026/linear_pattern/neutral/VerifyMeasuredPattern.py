from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
from zlib import ZLIB_RUNTIME_VERSION


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src")]
from ProveSharedPatternEmission import read_presentation

FIXTURE = ROOT / "re/solidworks/v2026/corpus/linear-pattern"
FORMAT = "solidworks.sldprt"
MEASURE = "solidworks_native_measurement"
PRESENTATION = "solidworks_pattern_presentation"
PACKETS = (
    ("MeasuredCold01", "da60bbfdc5411448b9aa5cd06c2a8772a0e0f2c39efa14ba2dc336c625e32cb1",
     "ae4f5853e4066a0d3f00cf4cbdaac12797b18c55c268ada6431d7e062bd5d23b"),
    ("MeasuredZlibNg01", "9e8456c5f266646e7a96ffa711c5a4e3be957ffa807eaddc4e9aa8e0dae8bf8c",
     "c119cfd3f1faef104030333cab7c55221f890ea52dc3a853b115e8e4108ec0c4"),
)


def require(predicate, message):
    if not predicate:
        raise ValueError(message)


def finger(data):
    return sha256(data).hexdigest()


def pinned_receipt(name, packet_sha, result_sha):
    fixture = FIXTURE / name
    packet = (fixture / "Packet.json").read_bytes()
    tracked = (fixture / "Result.json").read_bytes()
    report = json.loads(tracked)
    result = (json.dumps(report, indent=2) + "\n").replace("\n", "\r\n").encode()
    require(finger(packet) == packet_sha and finger(result) == result_sha and b"\r" not in tracked,
            "disclosed packet custody changed")
    files = json.loads(packet)["files"]
    require(report["packet_sha256"] == packet_sha and report["build_sha256"] == files["Build.json"],
            "native result no longer binds its original packet")
    if name == "MeasuredZlibNg01":
        require(finger((fixture / "Compression.json").read_bytes()) == files["Compression.json"],
                "the alternate compression record changed")
    return files, report, {"packet": packet, "result": result}, tracked


@contextmanager
def no_reads(folder):
    rejected = []
    active = True

    def audit(event, values):
        if not active:
            return
        if event == "open" and isinstance(values[0], str):
            path = Path(values[0])
            if path.is_relative_to(folder) and path.is_dir():
                return
        if event == "open" or event.startswith(("os.exec", "os.spawn", "socket.")) or event in (
            "subprocess.Popen", "os.startfile", "os.system", "os.posix_spawn", "ctypes.dlopen"
        ):
            rejected.append(event)
            raise RuntimeError("unexpected runtime input or application launch during measured pattern proof: " + event)

    sys.addaudithook(audit)
    try:
        yield rejected
    finally:
        active = False


def refuse(operation, sink, message):
    before = sink.getvalue(), sink.tell()
    try:
        operation(sink)
    except (ValueError, TypeError, RuntimeError) as error:
        require(message in str(error), "unexpected refusal: " + str(error))
    else:
        raise ValueError("unqualified pattern published")
    require((sink.getvalue(), sink.tell()) == before, "unqualified pattern mutated output")


def check_shape(readback, original, phase):
    from interchange.Features.FeatureKinds import LinearPattern

    pattern, = (item for item in readback.feature_timeline if type(item.definition) is LinearPattern)
    owned = {item.id: item for item in readback.parameters}
    count, pitch = (owned[key] for key in pattern.parameter_ids)
    expected = original.feature_timeline[-1].definition
    body, = readback.bodies
    topology = body.topology
    measured = phase["cold_geometry"]
    mass = measured["mass"]
    require(readback.brep is not None and not readback.brep_payloads and len(readback.selections) == 7
            and body.final_feature_id == pattern.id and count.owner_id == pitch.owner_id == pattern.id
            and count.name == "D1" and count.value.value == expected.instance_count
            and pitch.name == "D3" and pitch.value == pattern.definition.spacing and pitch.value.unit == "mm"
            and isclose(pitch.value.value, expected.spacing.value * 1000.0)
            and pattern.definition.reversed == expected.reversed, "cold read missed a live pattern owner or driver")
    config, = readback.configurations
    require(config.active and config.name == original.configurations[0].name, "cold read lost the active configuration")
    require(topology.solid_count == measured["body_count"] == 1
            and topology.face_count == measured["face_count"]
            and isclose(topology.volume, mass["volume"] * 1e9, rel_tol=5e-7)
            and isclose(topology.surface_area, mass["area"] * 1e6, rel_tol=5e-7)
            and all(isclose(actual, target * 1000.0, rel_tol=5e-7) for actual, target in zip(
                body.attributes["solidworks.body_centroid_mm"], mass["com"], strict=True
            )), "strict solid differs from native measures")
    axis = ["horizontal", "horizontal", "vertical", "vertical"]
    require(len(readback.sketches) == len(original.sketches) == 2, "missing stock sketch")
    for model, recovered in zip(original.sketches, readback.sketches, strict=True):
        require(sorted(row.kind for row in model.constraints) == axis and not model.parameter_ids
                and sorted(row.kind for row in recovered.constraints if row.kind in axis) == axis,
                "lost the authored stock axes")
    readback.assert_valid()
    return {"faces": topology.face_count, "volume_mm3": topology.volume, "area_mm2": topology.surface_area,
            "count": count.value.value, "pitch_mm": pitch.value.value,
            "sdk_sketch_relations": [[row.kind for row in sketch.constraints] for sketch in readback.sketches]}


def verify(name, scratch):
    from convert import open_document, write_document
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks import SldprtAdapter
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.Patterns.PrepPatPart import PrepPatPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange import CadDocument

    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    receipts = [pinned_receipt(*pin) for pin in PACKETS]
    original = FIXTURE / PACKETS[0][0]
    request_bytes = (original / (name + "Request.json")).read_bytes()
    request = json.loads(request_bytes)
    authored = CadDocument.from_json(json.dumps(request["document"]))
    presentation = read_presentation(request["presentation"])
    native_path, epoch = (request["target"][key] for key in ("PathName", "SavedAt"))
    target_name = name + ".SLDPRT"
    witness = json.loads((original / "Streams.json").read_bytes())
    require(witness["source_build_sha256"] == receipts[0][0]["Build.json"]
            and witness["cases"][name]["container"]["sha256"] == receipts[0][0][target_name],
            "stream witness no longer binds the classic measured output")
    expected_streams = witness["cases"][name]["streams"]
    bare = {"final_destination": native_path, "require_native_transfers": True}

    def public(document, sink, options):
        return write_document(document, sink, destination_format=FORMAT, allow_carrier=False, values=options)

    def direct(document, sink, options):
        return SldprtWriter().write(document, sink, WriteOptions(values=options))

    def adapter(document, sink, options):
        return SldprtAdapter().write(document, sink, WriteOptions(values=options))

    target = scratch / target_name
    launches = (public, direct, adapter)
    refusals = 0
    with target.open("xb") as owned_file, no_reads(scratch) as denied:
        payload = PrepPatPart(authored, BytesIO(), epoch, WriteOptions(values=bare), PresentValue=presentation).BytesValue
        digest = finger(payload)
        matches = tuple(index for index, row in enumerate(receipts) if row[0][target_name] == digest)
        streams = {record.name: [len(record.data), finger(record.data)] for record in SldprtArchive.from_bytes(payload).records}
        require(streams == expected_streams, "generated logical streams differ from the measured witness")
        if not matches:
            for _, _, evidence, _ in receipts:
                options = {**bare, PRESENTATION: presentation, MEASURE: {"written_at": epoch, "receipt": evidence}}
                for writer in launches:
                    refuse(lambda sink: writer(authored, sink, options), BytesIO(), "no exact native linear pattern measurement")
                    refusals += 1
            return {"case": name, "status": "unmeasured_compressor_refused", "generated_sha256": digest,
                    "runtime": ZLIB_RUNTIME_VERSION, "runtime_reads": len(denied), "publications": 0, "refusals": refusals}
        enum, = matches
        _, native, evidence, normalized = receipts[enum]
        case_values = {**bare, PRESENTATION: presentation, MEASURE: {"written_at": epoch, "receipt": evidence}}
        sinks = [BytesIO() for _ in launches]
        outcomes = [writer(authored, sink, case_values) for writer, sink in zip(launches, sinks, strict=True)]
        outcomes.append(public(authored, owned_file, case_values))
        require(all(sink.getvalue() == payload for sink in sinks), "public model's matched archives differed")
        lf_receipt = {**evidence, "result": normalized}
        mixed_receipt = {**evidence, "result": normalized.replace(b"\n", b"\r\n", 1)}
        changed_result = {**evidence, "result": b"{}"}
        alternate = receipts[1 - enum][2]
        for writer in (public, direct):
            sink = BytesIO()
            outcomes.append(writer(authored, sink, {**case_values, MEASURE: {"written_at": epoch, "receipt": lf_receipt}}))
            require(sink.getvalue() == payload, "canonical LF receipt changed the model")
            for options, message in (
                ({**bare, PRESENTATION: presentation}, "requires an offline native measurement receipt"),
                ({**case_values, MEASURE: {"written_at": epoch, "receipt": changed_result}}, "exact disclosed native measurement"),
                ({**case_values, MEASURE: {"written_at": epoch, "receipt": mixed_receipt}}, "exact disclosed native measurement"),
                ({**case_values, MEASURE: {"written_at": epoch, "receipt": alternate}}, "no exact native linear pattern measurement"),
                ({**case_values, MEASURE: {"written_at": epoch + 1, "receipt": evidence}}, "no exact native linear pattern measurement"),
                ({**case_values, "final_destination": rf"C:\Elsewhere\{target_name}"}, "no exact native linear pattern measurement"),
                ({**case_values, PRESENTATION: {}}, "explicit typed presentation"),
            ):
                refuse(lambda content: writer(authored, content, options), BytesIO(b"unchanged"), message)
                refusals += 1
        require(all(outcome.vendor_loadable and outcome.application_usable and not outcome.dropped
                    and outcome.native_capabilities == GetDocumentCaps(authored)
                    and outcome.metadata[MEASURE]["generated_sha256"] == digest
                    and outcome.metadata[MEASURE]["packet_sha256"] == finger(evidence["packet"])
                    and outcome.metadata[MEASURE]["native_result_sha256"] == finger(evidence["result"])
                    for outcome in outcomes), "publication lacks actual native transfer evidence")
        readback = open_document(BytesIO(payload), source_format=FORMAT, strict=True)
        shape = check_shape(readback, authored, native["phases"][name + "-edit"])
        old_values = {key: value for key, value in case_values.items() if key != PRESENTATION}
        refuse(lambda sink: public(readback, sink, old_values), BytesIO(b"untouched"), "does not support")
        refuse(lambda sink: direct(readback, sink, old_values), BytesIO(b"untouched"), "exact passing SOLIDWORKS")
        design = open_document(BytesIO(payload), source_format=FORMAT, strict=True, include_brep=False)
        for writer in (public, direct):
            refuse(lambda sink: writer(design, sink, old_values), BytesIO(b"untouched"), "native-only feature definitions")
        refusals += 4
        step = authored.feature_timeline[-1]
        pitch_id = step.parameter_ids[1]
        driver = next(value for value in authored.parameters if value.id == pitch_id)
        spacing = replace(driver.value, value=driver.value.value + 0.000125)
        edited = replace(
            authored,
            feature_timeline=(*authored.feature_timeline[:-1], replace(step, definition=replace(step.definition, spacing=spacing))),
            parameters=tuple(replace(value, value=spacing) if value is driver else value for value in authored.parameters),
        )
        for writer in (public, direct):
            refuse(lambda sink: writer(edited, sink, case_values), BytesIO(b"untouched"), "no exact native linear pattern measurement")
        refuse(lambda sink: write_document(edited, sink, destination_format=FORMAT, allow_carrier=True, values=case_values),
               BytesIO(b"untouched"), "no exact native linear pattern measurement")
        refusals += 3
        changed = replace(authored, metadata={**authored.metadata, "unsupported_authored_state": True})
        refuse(lambda sink: public(changed, sink, case_values), BytesIO(b"untouched"), "does not support")
        refuse(lambda sink: direct(changed, sink, case_values), BytesIO(b"untouched"), "only the ordinary neutral part name")
        refusals += 2
    require(target.read_bytes() == payload and not denied, "file stream differs or runtime attempted data access")
    persisted = open_document(target, source_format=FORMAT, strict=True)
    require(check_shape(persisted, authored, native["phases"][name + "-edit"]) == shape,
            "path and buffer selected different physical semantics")
    contrast = scratch / "WrongPath" / target_name
    contrast.parent.mkdir()
    contrast.write_bytes(b"older output")
    with no_reads(scratch) as denied:
        try:
            write_document(authored, contrast, values=case_values, overwrite=True, allow_carrier=False)
        except ValueError as error:
            require("no exact native linear pattern measurement" in str(error), "unexpected path refusal: " + str(error))
        else:
            raise ValueError("a different pathname published a measured pattern")
    require(not denied and contrast.read_bytes() == b"older output" and tuple(contrast.parent.iterdir()) == (contrast,),
            "wrong path changed output or left staging artifacts")
    return {"case": name, "status": "native_hash_reproduced", "runtime": ZLIB_RUNTIME_VERSION,
            "request_sha256": finger(request_bytes), "generated_sha256": digest,
            "packet_sha256": finger(evidence["packet"]), "result_sha256": finger(evidence["result"]),
            "streams": len(streams), "runtime_reads": len(denied), "native_processes": 0,
            "publications": len(outcomes), "refusals": refusals + 1, "strict_geometry": shape}


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the aggregate's measured fresh-neutral pattern publication")
    parser.add_argument("--case", choices=("ColdRaisedPatternA", "ColdRaisedPatternB"), required=True)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitMeasuredPatternPort-") as folder:
        print(json.dumps(verify(args.case, Path(folder).resolve()), sort_keys=True, allow_nan=False))
