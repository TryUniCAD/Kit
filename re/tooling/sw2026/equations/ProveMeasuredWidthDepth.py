from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parents[1]))

from CheckScopedPlainWriter import WriterAudit, reject

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
BASE = "c8d85d713dc357770115329e9f1bcb027dbfca4f"
NATIVE_RECEIPT = "re/solidworks/measurements/2026/SdkWidthDepthPreparationNative01.json"
PINS = {
    "Neutral.json": "90d9d22d737bd8d313a68d10eef1e3cb730bdae81c973a3656b591d627ad786b",
    "Trial.json": "538c128ae512d874d4673a19367e0d0fc6a0138ade258d880f71d34769e74ba1",
    "Result.json": "b544ff3d3668f7dc9815bd862b6d1f067174503cd310e4a7cff56ce8d8458ba2",
    "Build.json": "6ba37a11c412adb495cc7eb77fe107ad6f7b586addecc658609d1bf3198e3bda",
    NATIVE_RECEIPT: "f40bc2433d54bcb8c3ae5165b3a3965ebae4876c71cf52293ad4a045af85b420",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, key):
    raw = path.read_bytes()
    require(digest(raw) == PINS[key], f"disclosed evidence mismatch: {key}")
    return json.loads(raw)


def disclosed(packet, root):
    request = pinned(packet / "Neutral.json", "Neutral.json")
    trial = pinned(packet / "Trial.json", "Trial.json")
    native = pinned(packet / "Result.json", "Result.json")
    built = pinned(packet / "Build.json", "Build.json")
    receipt = pinned(root / NATIVE_RECEIPT, NATIVE_RECEIPT)
    require(native["passed"] and native["controls_healthy"]
            and native["same_encoded_native_locator"] and not native["heldout_acceptance"]
            and native["trial_sha256"] == receipt["trial_sha256"] == PINS["Trial.json"]
            and receipt["full_native_result_sha256"] == PINS["Result.json"]
            and trial["files_sha256"]["Build.json"] == receipt["build_sha256"] == PINS["Build.json"]
            and trial["files_sha256"]["Neutral.json"] == PINS["Neutral.json"]
            and request["sdk_created_at"] == built["sdk_created_at"]
            and request["settings"]["output"]["path_name"] == built["encoded_locator"]
            == trial["encoded_locator"]
            and not built["runtime_input_file_reads"], "disclosed source, build and oracle custody disagree")
    phases = native["phases"]
    require(set(phases) == {"ControlBefore", "PlainEdit", "PlainReopen", "ReferenceEdit",
                            "ReferenceReopen", "ControlAfter"}
            and len({(phase["oracle_identity"]["process_id"],
                      phase["oracle_identity"]["process_creation_filetime"])
                     for phase in phases.values()}) == native["distinct_native_processes"] == 6,
            "native comparison did not observe six independent process lifetimes")
    for name, phase in phases.items():
        identity = phase["oracle_identity"]
        status = phase["open_status"] if name.startswith("Control") else [
            phase["open_errors"], phase["open_warnings"]
        ]
        require(status == [0, 0] and phase["passed"] and not phase["dialogs"]
                and not phase["controller_diagnostics"] and identity["version_matches"]
                and identity["sha256"] == receipt["oracle_identity"]["sha256"],
                "native open, authority or control is incomplete")
    require(phases["ReferenceEdit"]["save_status"] == [True, 0, 0]
            and phases["ReferenceEdit"]["derivative_sha256"] == receipt["cases"]["Reference"]["saved_sha256"]
            and sum(phase.get("numeric_check_count", phase.get("numeric_checks", 0))
                    for phase in phases.values()) == 188
            and built["writer_receipts"]["Reference"]["sha256"]
            == trial["files_sha256"]["Frozen/Reference.SLDPRT"]
            == receipt["cases"]["Reference"]["generated_sha256"],
            "output and clean native edit/reopen evidence do not identify the same case")
    return request | {"receipt": receipt}


def author_document(request):
    from interchange import Expression, ParameterRole
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.geometry.Models.GeometryCurves import PointGeometry
    from interchange.geometry.Models.Sketch import ConstraintRef, SketchEntity, SketchRelation
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.serialization.Deserialize import FromData

    document = FromData(request["document"])
    (sketch,) = document.sketches
    (feature,) = document.feature_timeline
    width, _ = sketch.parameter_ids
    (depth,) = feature.parameter_ids
    require(request["equation"] == {"target": depth, "dependency": width, "divisor": 2},
            "actual disclosed relation owner differs")
    datum = SketchEntity("modeled-origin", GeometryKind.KPoint, PointGeometry(PlaneVector(0, 0)), True, True)
    anchor = SketchRelation("modeled-origin-coincidence", "coincident",
                            (ConstraintRef(datum.id), ConstraintRef(sketch.closed_profile_entity_ids[0][0], "start")))
    relation = Expression(f'"D1@{sketch.name}" / 2', (width,), "solidworks")
    return replace(document, sketches=(replace(sketch, entities=(*sketch.entities, datum),
                                               constraints=(*sketch.constraints, anchor)),),
                   parameters=tuple(replace(param, role=ParameterRole.KDerived, expression=relation)
                                    if param.id == depth else param for param in document.parameters))


def check_read(raw, width_mm=39.125, height_mm=17.375):
    from convert import open_document

    options = {"source_format": FORMAT, "configuration": "modeled default"}
    solid = open_document(BytesIO(raw), **options)
    design = open_document(BytesIO(raw), **options, include_brep=False)
    require(solid.brep is not None and not solid.brep_payloads and design.brep is None
            and design.parameters == solid.parameters and design.sketches == solid.sketches
            and design.feature_timeline == solid.feature_timeline and len(solid.feature_timeline) == 19,
            "design and geometry reads disagree on editable history")
    width, height, depth = solid.parameters
    depth_mm = width_mm / 2
    sketch, = solid.sketches
    body, = solid.bodies
    (boundary,) = solid.brep.bodies
    require((width.id, height.id, depth.id)
            == ("sldprt:parameter:18:D1", "sldprt:parameter:18:D2", "sldprt:parameter:21:D1")
            and (width.value.value, height.value.value, depth.value.value) == (width_mm, height_mm, depth_mm)
            and width.role.value == height.role.value == "driving"
            and depth.role.value == "derived" and depth.expression.source == f'"D1@{sketch.name}" / 2'
            and depth.expression.parameter_ids == (width.id,)
            and sketch.parameter_ids == (width.id, height.id)
            and len(sketch.entities) == 5 and [row.kind for row in sketch.constraints]
            == ["horizontal", "vertical", "horizontal", "vertical", "distance", "distance", "coincident"]
            and sketch.entities[-1].fixed and sketch.entities[-1].construction
            and body.final_feature_id == depth.owner_id and boundary.design_body_id == body.id,
            "strict read lost the physical dimension, origin or body owner")
    evidence = solid.metadata["solidworks.typed_width_depth"]
    target = evidence["target"]["live_handle"]
    dependency = evidence["dependency"]["live_handle"]
    require(dependency["object_index"] != target["object_index"]
            and evidence["target"]["component"] != evidence["dependency"]["component"],
            "strict relation lost typed live dimension identity")
    topology = body.topology
    require((topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count)
            == (1, 6, 12, 8) and isclose(topology.volume, width_mm * height_mm * depth_mm)
            and all(isclose(observed, expected) for observed, expected in
                    zip(body.attributes["solidworks.body_centroid_mm"], (width_mm / 2, height_mm / 2, depth_mm / 2), strict=True)),
            "reader geometry failed independent rectangular prism measures")
    return solid


def changed_config(candidate, *, trailing=False, disabled=False, divisor=None):
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(candidate)
    config = "Contents/Config-0"
    if trailing:
        data = archive.streams[config] + b"\x00"
    else:
        link = ReadNativeLink(archive, 0, RelationConfig="modeled default").ConfigValue
        manager = link.RootValue.FieldsValue["f9d0"]
        fields = manager.FieldsValue["f58"]["items"][0]["o"].FieldsValue
        if disabled:
            fields["f18"] = 0
        if divisor is not None:
            side = fields["f60"].FieldsValue
            value = side["f10"]["items"][-1]["o"]
            require(fields["f10"].endswith(" / 2") and side["f50"].endswith(" / 2")
                    and value.FieldsValue["f08"] == "2", "case requires the actual authored divisor")
            fields["f10"] = fields["f10"][:-1] + divisor
            side["f50"] = side["f50"][:-1] + divisor
            value.FieldsValue["f08"] = divisor
        data, _ = WriteConfigMut(link.RootValue, link.VersionValue, link.HeaderValue, PartRelations=True)
    return BuildSldprt(archive.streams | {config: data}, FileId=archive.file_id,
                      FormatVersion=archive.format_version)


def boss_depth(model):
    boss, = (step for step in model.feature_timeline if step.name == "Boss-Extrude1")
    depth, = (parameter for parameter in model.parameters if parameter.owner_id == boss.id and parameter.name == "D1")
    return depth


def inspect_inactive(model, raw):
    depth = boss_depth(model)
    require(len(model.feature_timeline) == 19 and "solidworks.typed_width_depth" not in model.metadata
            and depth.expression is None and depth.role.value == "driving"
            and model.source.sha256 == digest(raw)
            and any("width-depth history is unresolved" in value.message for value in model.diagnostics),
            "partial inspection credited an unqualified relation or lost its source")


def check_bad_graph(candidate):
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks.Container.Container import SldprtFormatError
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter

    cases = {"trailing_config": {"trailing": True}, "unqualified_mode": {"disabled": True}}
    for change in cases.values():
        malformed = changed_config(candidate, **change)
        for include in (False, True):
            reject(lambda: open_document(BytesIO(malformed), source_format=FORMAT, include_brep=include),
                   SldprtFormatError, "local SOLIDWORKS width-depth history is unresolved")
        inspect_inactive(open_document(BytesIO(malformed), source_format=FORMAT, include_brep=False, strict=False),
                         malformed)
    disabled = changed_config(candidate, disabled=True)
    raw_options = ReadOptions(include_brep=True, extract_raw_brep=True, strict=False)
    inspect_inactive(SldprtAdapter().read(BytesIO(disabled), raw_options), disabled)
    return [*(f"{case}_{stage}" for case in cases for stage in ("strict_geometry", "strict_design", "partial_diagnostic")),
            "unqualified_mode_raw_diagnostic"]


def check_generic_formula(candidate):
    from convert import open_document

    alternate = changed_config(candidate, divisor="3")
    inspection = open_document(BytesIO(alternate), source_format=FORMAT, include_brep=False, strict=False)
    depth = boss_depth(inspection)
    require("solidworks.typed_width_depth" not in inspection.metadata
            and not any("width-depth history is unresolved" in value.message for value in inspection.diagnostics)
            and depth.expression is not None and depth.expression.source == '"D1@Sketch1" / 3',
            "unrelated formula did not stay on legacy inspection")
    return True


def varied_recipe(doc, *, width_mm=None, rename=True):
    (sketch,) = doc.sketches
    old_width, _ = sketch.parameter_ids
    depth, = (param for param in doc.parameters if param.expression is not None)
    width, = (param for param in doc.parameters if param.id == old_width)
    boss, = doc.feature_timeline
    width_value = replace(width.value, value=width.value.value + 1 if width_mm is None else width_mm)
    depth_value = replace(depth.value, value=width_value.value / 2)
    new_sketch = replace(sketch, name=sketch.name + " Contrast") if rename else sketch
    points = []
    for entity in new_sketch.entities:
        curve = entity.geometry
        if entity.kind.value == "line":
            start, end = (replace(point, x=width_value.value) if point.x == width.value.value else point
                          for point in (curve.start, curve.end))
            entity = replace(entity, geometry=replace(curve, start=start, end=end))
        points.append(entity)
    dependent = replace(depth, value=depth_value,
                        expression=replace(depth.expression, source=f'"D1@{new_sketch.name}" / 2'))
    return replace(doc, sketches=(replace(new_sketch, entities=tuple(points)),),
                   feature_timeline=(replace(boss, definition=replace(boss.definition, length=depth_value)),),
                   parameters=tuple(dependent if param is depth else
                                    replace(width, value=width_value) if param is width else
                                    param for param in doc.parameters))


def reject_public(doc, readback, request, values, target, audit):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    writer = SldprtWriter()
    stream = BytesIO(b"preserve stream")
    stream.seek(3)
    original_opens = audit.target_opens
    authority = values[OPTION]
    altered = deepcopy(authority)
    altered["receipt"]["controls_healthy"] = False
    (sketch,) = doc.sketches
    depth, = (param for param in doc.parameters if param.expression is not None)
    wrong_ref = replace(depth, expression=replace(depth.expression, parameter_ids=(sketch.parameter_ids[1],)))
    wrong_dependency = replace(doc, parameters=tuple(wrong_ref if param is depth else param for param in doc.parameters))
    missing_anchor = replace(doc, sketches=(replace(sketch, constraints=sketch.constraints[:-1]),))
    altered_source = replace(readback, metadata={**readback.metadata, "unexpected_record": True})
    cases = (
        ("no_receipt", doc, {key: value for key, value in values.items() if key != OPTION},
         ValueError, "offline native measurement receipt"),
        ("changed_receipt", doc, values | {OPTION: altered}, ValueError, "authenticated width-depth report"),
        ("changed_epoch", doc, values | {OPTION: authority | {"written_at": request["sdk_created_at"] + 1}},
         ValueError, "differs from the measured width-depth output"),
        ("stale_readback", altered_source, values, ValueError, "cold readback differs from its regenerated part"),
    )
    for _, model, options, error, reason in cases:
        reject(lambda: write_document(model, target, values=options, overwrite=True), error, reason)
        reject(lambda: writer.write(model, stream, WriteOptions(values=options)), error, reason)
    for model, reason in ((wrong_dependency, "reference the actual width"), (missing_anchor, "active origin coincidence")):
        reject(lambda: write_document(model, target, values=values, overwrite=True, destination_format=FORMAT),
               NotFoundError, "does not support the destination")
        reject(lambda: writer.write(model, stream, WriteOptions(values=values)), ValueError, reason)
    reject(lambda: write_document(doc, target, values=values, overwrite=True, configuration="Other"),
           ValueError, "requested write configuration is unavailable")
    wrong_path = values | {"final_destination": "C:\\Unmeasured\\" + target.name}
    reject(lambda: writer.write(doc, stream, WriteOptions(values=wrong_path)),
           ValueError, "differs from the measured width-depth output")
    require(audit.target_opens == original_opens and stream.getvalue() == b"preserve stream"
            and stream.tell() == 3, "refused operation touched a caller output")
    return [*(case[0] for case in cases), "wrong_dependency", "missing_origin_coincidence",
            "wrong_configuration", "different_locator"]


def worker(root, request, directory, portable=False):
    sys.path.insert(0, str(root / "src"))
    target = directory / (request["document"]["metadata"]["name"] + ".SLDPRT")
    audit = WriterAudit(root / "src", target)
    sys.addaudithook(audit.observe)
    from convert import extract_brep, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive, SldprtFormatError
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.Enums.EnumDocument import Capability

    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    doc = author_document(request)
    path = request["settings"]["output"]["path_name"]
    epoch = request["sdk_created_at"]
    values = {OPTION: {"written_at": epoch, "receipt": request["receipt"]},
              "final_destination": path, "require_native_transfers": True}
    writer = SldprtWriter()
    expected = request["receipt"]["cases"]["Reference"]["generated_sha256"]
    audit.phase = "done"
    target.write_bytes(b"preserve path")
    try:
        audit.phase = "write"
        candidate = PrepareNative(doc, BytesIO(), epoch, WriteOptions(values={"final_destination": path}))
        raw = candidate.BytesValue
        actual = digest(raw)
        exact_archive = actual == expected
        actual_streams = SldprtArchive.from_bytes(raw).streams
        require(actual_streams == candidate.StreamsValue, "container changed the constructed logical streams")
        stream_hashes = {name: digest(data) for name, data in actual_streams.items()}
        if portable:
            require(stream_hashes == request["stream_sha256"], "portable request changed the measured logical streams")
        else:
            require(exact_archive and len(raw) == 9157, "constructed bytes differ from measured native file")
        readback = check_read(raw)
        history_refusals = check_bad_graph(raw)
        width_probe = 20.01
        width_contrast = varied_recipe(doc, width_mm=width_probe, rename=False)
        rounded = PrepareNative(width_contrast, BytesIO(), epoch, WriteOptions(values={"final_destination": path}))
        design = check_read(rounded.BytesValue, width_mm=width_probe)
        reread = PrepareNative(design, BytesIO(), epoch, WriteOptions(values={"final_destination": path}))
        require(reread.BytesValue == rounded.BytesValue, "adjacent inverse conversion changed the strict readback bytes")
        width_metres = width_probe * .001
        require(width_metres * 1000 != width_probe == width_metres / .001,
                "independent width contrast does not distinguish the inverse conversion")
        variant = varied_recipe(doc)
        variant_part = PrepareNative(variant, BytesIO(), epoch, WriteOptions(values={"final_destination": path}))
        variant_lengths = {stream: len(variant_part.StreamsValue[stream])
                           for stream in ("Contents/Config-0", "Contents/Config-0-ResolvedFeatures")}
        require(all(length != len(candidate.StreamsValue[stream]) for stream, length in variant_lengths.items())
                and digest(variant_part.BytesValue) != expected,
                "independent neutral dimensions and labels did not change real archive streams")
        rechecked = BytesIO()
        for model in (variant, width_contrast):
            reject(lambda: write_document(model, rechecked, destination_format=FORMAT,
                                          values=values, allow_carrier=False),
                   ValueError, "differs from the measured width-depth output")
            reject(lambda: writer.write(model, rechecked, WriteOptions(values=values)),
                   ValueError, "differs from the measured width-depth output")
        require(not rechecked.getvalue(), "unmeasured neutral variant reached publication")
        refusals = reject_public(doc, readback, request, values, target, audit)
    finally:
        audit.phase = "done"
    generic_formula = check_generic_formula(raw)
    require(target.read_bytes() == b"preserve path" and tuple(directory.iterdir()) == (target,),
            "negative publication left file or staging changes")
    try:
        audit.phase = "write"
        results = []
        for model in (doc, readback):
            for direct in (False, True):
                sink = BytesIO()
                action = (lambda: writer.write(model, sink, WriteOptions(values=values))) if direct else (
                    lambda: write_document(model, sink, destination_format=FORMAT, allow_carrier=False, values=values)
                )
                if exact_archive:
                    results.append(action())
                    require(sink.getvalue() == raw, "native stream changed with write entrypoint or cold source")
                else:
                    reject(action, ValueError, "differs from the measured width-depth output")
                    require(not sink.getvalue() and sink.tell() == 0, "alternate physical bytes reached the stream")
        if sys.platform != "win32":
            if exact_archive:
                results.append(write_document(doc, target, overwrite=True, allow_carrier=False, values=values))
            else:
                reject(lambda: write_document(doc, target, overwrite=True, allow_carrier=False, values=values),
                       ValueError, "differs from the measured width-depth output")
    finally:
        audit.phase = "done"
    require(all(result.vendor_loadable and result.application_usable and not result.dropped
                and Capability.KExpressions in result.native_capabilities
                and result.metadata[OPTION]["generated_sha256"] == expected
                for result in results)
            and target.read_bytes() == (raw if exact_archive and sys.platform != "win32" else b"preserve path")
            and audit.target_opens == int(exact_archive and sys.platform != "win32")
            and not audit.denied and tuple(directory.iterdir()) == (target,),
            "publication, capability transfer or runtime guard failed")
    reject(lambda: extract_brep(raw, directory / "raw", source_format=FORMAT),
           SldprtFormatError, "SLDPRT contains no readable Parasolid payload")
    require(not (directory / "raw").exists(), "raw extraction invented a cache")
    return {"bytes": len(raw), "sha256": actual, "matches_measured_archive": exact_archive,
            "file_opens": audit.target_opens,
            "guarded_runtime_input_reads": len(audit.denied), "published_routes": len(results),
            "config_map_counter": candidate.ConfigValue.MapValue.CounterValue,
            "resolved_map_counter": candidate.ResolvedValue.MapValue.CounterValue,
            "stream_lengths": {name: len(data) for name, data in candidate.StreamsValue.items()},
            "stream_sha256": stream_hashes,
            "unrelated_formula_legacy_inspection": generic_formula,
            "width_inverse": {
                "width_mm": 20.01, "depth_mm": 10.005,
                "strict_readback_regenerated": True, "publication_refused": True,
            },
            "parameter_ids": [param.id for param in readback.parameters],
            "feature_rows": len(readback.feature_timeline),
            "unmeasured_variant_stream_lengths": variant_lengths,
            "refusals": [*refusals, "raw_cache", "unmeasured_neutral_variant", *history_refusals]}


def supervise(root, packet, target):
    request = disclosed(packet, root)
    reports = []
    for _ in range(2):
        run = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--root", str(root), "--worker"],
                             input=json.dumps(request), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, timeout=90, check=False)
        require(run.returncode == 0 and not run.stderr, run.stderr)
        reports.append(json.loads(run.stdout))
    require(reports[0] == reports[1], "fresh independent workers disagree")
    paths = set()
    for query in (["diff", "--name-only", "-z", BASE, "--", "src"],
                  ["ls-files", "--others", "--exclude-standard", "-z", "--", "src"]):
        paths.update(subprocess.check_output(["git", *query], cwd=root).decode().split("\0"))
    evidence = {"schema": "kit.sw2026.measured-public-width-depth.v1",
                "base": BASE, "native_launches": 0,
                "previous_native_processes": 6, "previous_native_numeric_checks": 188, "heldout_inputs_read": 0,
                "guards": {"processes": 2, **reports[0]}, "disclosed_hashes": PINS,
                "method_sha256": digest(HERE.read_bytes()),
                "source_sha256": {path: digest((root / path).read_bytes()) for path in sorted(set(paths) - {""})}}
    with target.open("x", encoding="utf-8") as output:
        json.dump(evidence, output, indent=2, sort_keys=True)
        output.write("\n")
    print(digest(target.read_bytes()))


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--disclosed", type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--worker", action="store_true")
    cli.add_argument("--portable", action="store_true")
    args = cli.parse_args()
    if args.worker:
        with TemporaryDirectory(prefix="KitMeasuredWidthDepth-") as temp:
            print(json.dumps(worker(args.root, json.load(sys.stdin), Path(temp).resolve(), args.portable), sort_keys=True))
    else:
        if args.portable:
            cli.error("--portable requires --worker")
        supervise(args.root, args.disclosed, args.output)
