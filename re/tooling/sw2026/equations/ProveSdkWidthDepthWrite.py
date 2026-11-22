from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
from subprocess import run
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parents[1]))

from CheckScopedPlainWriter import WriterAudit, reject

PACKET = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover/WidthDepthSameLocator04")
NEUTRAL = "90d9d22d737bd8d313a68d10eef1e3cb730bdae81c973a3656b591d627ad786b"
NATIVE = "b544ff3d3668f7dc9815bd862b6d1f067174503cd310e4a7cff56ce8d8458ba2"
EXPECTED = "5783b3944d76563ae8143b8789a923f1b07fb4eb94f4b59fef50b6b80ac696b6"
RECEIPT_PATH = "re/solidworks/measurements/2026/SdkWidthDepthPreparationNative01.json"
RECEIPT_SHA = "f40bc2433d54bcb8c3ae5165b3a3965ebae4876c71cf52293ad4a045af85b420"
FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
FAULTS = (
    "missing_coincidence", "wrong_corner", "height_dependency",
    "unavailable_configuration", "unmodeled_metadata", "missing_receipt",
    "changed_receipt", "different_width", "different_epoch", "different_locator", "stale_readback",
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def pinned(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, f"disclosed input changed: {path.name}")
    return json.loads(data)


def disclosed(packet):
    neutral = pinned(packet / "Neutral.json", NEUTRAL)
    native = pinned(packet / "Result.json", NATIVE)
    receipt = pinned(ROOT / RECEIPT_PATH, RECEIPT_SHA)
    trial = pinned(packet / "Trial.json", receipt["trial_sha256"])
    build = pinned(packet / "Build.json", receipt["build_sha256"])
    require(
        native["passed"] and native["controls_healthy"]
        and native["distinct_native_processes"] == 6
        and native["same_encoded_native_locator"] and not native["heldout_acceptance"]
        and receipt["full_native_result_sha256"] == NATIVE
        and trial["encoded_locator"] == build["encoded_locator"] == neutral["settings"]["output"]["path_name"]
        and build["sdk_created_at"] == neutral["sdk_created_at"] and not build["runtime_input_file_reads"]
        and receipt["cases"]["Reference"]["generated_sha256"] == EXPECTED
        == build["writer_receipts"]["Reference"]["sha256"]
        == trial["files_sha256"]["Frozen/Reference.SLDPRT"],
        "disclosed build, receipt, or measured candidate custody changed",
    )
    return {**neutral, "receipt": receipt}


def check_history(raw):
    from convert import open_document

    solid = open_document(raw, source_format=FORMAT)
    design = open_document(raw, source_format=FORMAT, include_brep=False)
    width, height, depth = solid.parameters
    sketch, = solid.sketches
    body, = solid.bodies
    carrier, = solid.brep.bodies
    relation = solid.metadata["solidworks.typed_resolved_semantics"]["local_width_depth_equation"]
    require(
        (width.value.value, height.value.value, depth.value.value) == (39.125, 17.375, 19.5625)
        and depth.role.value == "derived" and depth.expression.parameter_ids == (width.id,)
        and width.role.value == height.role.value == "driving"
        and depth.expression.source == '"D1@Sketch1" / 2'
        and sketch.parameter_ids == (width.id, height.id)
        and tuple(item.kind for item in sketch.constraints) == (
            "horizontal", "vertical", "horizontal", "vertical", "distance", "distance", "coincident",
        )
        and body.final_feature_id == depth.owner_id
        and carrier.design_body_id == body.id
        and relation["target"]["live_handle"] != relation["dependency"]["live_handle"]
        and body.topology.volume == 13298.5263671875
        and (body.topology.face_count, body.topology.edge_count, body.topology.vertex_count) == (6, 12, 8)
        and not solid.brep_payloads and design.brep is None and not design.brep_payloads
        and design.parameters == solid.parameters and design.sketches == solid.sketches
        and len(solid.feature_timeline) == 19
        and tuple((row.id, row.definition) for row in design.feature_timeline)
        == tuple((row.id, row.definition) for row in solid.feature_timeline),
        "strict public read lost independently bound owners, profile or geometry",
    )
    return solid


def change_width(doc, width_mm):
    from interchange.geometry.Models.GeometryCurves import LineGeometry

    sketch, = doc.sketches
    boss, = doc.feature_timeline
    width = next(row for row in doc.parameters if row.id == sketch.parameter_ids[0])
    depth = next(row for row in doc.parameters if row.id in boss.parameter_ids)
    width_value = replace(width.value, value=width_mm)
    depth_value = replace(depth.value, value=width_mm / 2)
    edges = []
    for edge in sketch.entities:
        line = edge.geometry
        if isinstance(line, LineGeometry):
            start = replace(line.start, x=width_mm) if line.start.x == width.value.value else line.start
            end = replace(line.end, x=width_mm) if line.end.x == width.value.value else line.end
            edge = replace(edge, geometry=replace(line, start=start, end=end))
        edges.append(edge)
    return replace(
        doc,
        sketches=(replace(sketch, entities=tuple(edges)),),
        feature_timeline=(replace(boss, definition=replace(boss.definition, length=depth_value)),),
        parameters=tuple(replace(row, value=width_value) if row is width else
                         replace(row, value=depth_value) if row is depth else row for row in doc.parameters),
    )


def fault_case(doc, readback, options, fault):
    from interchange.geometry.Models.Sketch import ConstraintRef

    sketch, = doc.sketches
    match fault:
        case "missing_coincidence":
            doc = replace(doc, sketches=(replace(sketch, constraints=sketch.constraints[:-1]),))
        case "wrong_corner":
            anchor = sketch.constraints[-1]
            second = ConstraintRef(sketch.closed_profile_entity_ids[0][1], "start")
            moved = replace(anchor, references=(anchor.references[0], second))
            doc = replace(doc, sketches=(replace(sketch, constraints=(*sketch.constraints[:-1], moved)),))
        case "height_dependency":
            depth, = (row for row in doc.parameters if row.expression is not None)
            wrong = replace(depth, expression=replace(depth.expression, parameter_ids=(sketch.parameter_ids[1],)))
            doc = replace(doc, parameters=tuple(wrong if row is depth else row for row in doc.parameters))
        case "unmodeled_metadata":
            doc = replace(doc, metadata={**doc.metadata, "unmodeled": True})
        case "missing_receipt":
            options = {key: value for key, value in options.items() if key != OPTION}
        case "changed_receipt":
            options = deepcopy(options)
            options[OPTION]["receipt"]["controls_healthy"] = False
        case "different_width":
            doc = change_width(doc, 20.01)
        case "different_epoch":
            options = {**options, OPTION: {**options[OPTION], "written_at": options[OPTION]["written_at"] + 1}}
        case "different_locator":
            options = {**options, "final_destination": "C:\\Unmeasured\\WidthDepthSameLocator04.SLDPRT"}
        case "stale_readback":
            doc = replace(readback, metadata={**readback.metadata, "unmodeled": True})
    config = "unavailable" if fault == "unavailable_configuration" else None
    return doc, options, config


def check_refusals(doc, readback, options):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    reasons = {
        "missing_coincidence": ("does not support the destination", "active origin coincidence"),
        "wrong_corner": ("does not support the destination", "actual starting corner"),
        "height_dependency": ("does not support the destination", "reference the actual width"),
        "unavailable_configuration": ("requested write configuration is unavailable",) * 2,
        "unmodeled_metadata": ("does not support the destination", "unprojected document metadata"),
        "missing_receipt": ("offline native measurement receipt",) * 2,
        "changed_receipt": ("authenticated width-depth report",) * 2,
        "different_width": ("differs from the measured width-depth output",) * 2,
        "different_epoch": ("differs from the measured width-depth output",) * 2,
        "different_locator": ("differs from the measured width-depth output",) * 2,
        "stale_readback": ("cold readback differs from its regenerated part",) * 2,
    }
    rows = {}
    for fault in FAULTS:
        model, values, configuration = fault_case(doc, readback, options, fault)
        registry, direct = reasons[fault]
        sink = BytesIO(b"untouched")
        sink.seek(3)
        rows[fault] = [
            reject(lambda: write_document(model, sink, destination_format=FORMAT, configuration=configuration,
                                          allow_carrier=False, values=values), (ValueError, NotFoundError), registry),
            reject(lambda: SldprtWriter().write(model, sink, WriteOptions(configuration=configuration, values=values)),
                   ValueError, direct),
        ]
        require(sink.getvalue() == b"untouched" and sink.tell() == 3, "a refused writer touched the stream")
    return rows


def assert_result(result, data):
    from interchange.Enums.EnumDocument import Capability

    require(
        result.vendor_loadable and result.application_usable and not result.dropped
        and not result.requirements and Capability.KExpressions in result.native_capabilities
        and result.bytes_written == 9157 == len(data) and digest(data) == EXPECTED
        and result.metadata[OPTION]["generated_sha256"] == EXPECTED,
        "publication did not preserve the measured output and native expression transfer",
    )


def worker(request, target):
    sys.path[:0] = list(map(str, (HERE.parent, ROOT / "src")))
    audit = WriterAudit(ROOT / "src", target)
    sys.addaudithook(audit.observe)

    from BuildSdkWidthDepth import author_document
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    for module in (
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.FilterMetadata",
        "interchange.document.Behavior.DocumentIo",
        "interchange.brep.Validation.BrepValidate",
    ):
        import_module(module)
    for codec in ("utf-16-le", "utf-8", "latin-1", "cp1252"):
        lookup(codec)

    doc = author_document(request)
    epoch = request["sdk_created_at"]
    values = {
        "final_destination": request["settings"]["output"]["path_name"],
        "require_native_transfers": True,
        OPTION: {"written_at": epoch, "receipt": request["receipt"]},
    }
    audit.phase = "write"
    try:
        prepared = PrepareNative(doc, BytesIO(), epoch, WriteOptions(values={"final_destination": values["final_destination"]}))
        raw = prepared.BytesValue
        archive = SldprtArchive.from_bytes(raw)
        require(digest(raw) == EXPECTED and len(raw) == 9157
                and archive.streams == prepared.StreamsValue and len(archive.streams) == 10,
                "current neutral generation did not reproduce the exact measured archive")
        readback = check_history(raw)
        checked = check_refusals(doc, readback, values)
        serialized = BytesIO()
        write_document(doc, serialized, destination_format="interchange.json")
        portable = open_document(serialized.getvalue(), source_format="interchange.json")
        require(portable == doc, "the neutral JSON path changed the authored design")
        writer = SldprtWriter()
        routes = 0
        for model in (doc, portable, readback):
            for is_direct in (False, True):
                sink = BytesIO()
                if is_direct:
                    result = writer.write(model, sink, WriteOptions(values=values))
                else:
                    result = write_document(model, sink, destination_format=FORMAT, allow_carrier=False, values=values)
                assert_result(result, sink.getvalue())
                routes += 1
        if sys.platform != "win32":
            path_result = write_document(doc, target, allow_carrier=False, values=values)
            routes += 1
    finally:
        audit.phase = "done"
    if sys.platform != "win32":
        assert_result(path_result, target.read_bytes())
        require(audit.target_opens == 1 and tuple(target.parent.iterdir()) == (target,),
                "inferred output did not publish exactly one proven staged file")
    require(not audit.denied, "runtime file, process, or service access occurred")
    return {
        "sha256": digest(raw), "bytes": len(raw), "published_routes": routes,
        "stream_sha256": {name: digest(data) for name, data in archive.streams.items()},
        "config_map_counter": prepared.ConfigValue.MapValue.CounterValue,
        "resolved_map_counter": prepared.ResolvedValue.MapValue.CounterValue,
        "runtime_reads": len(audit.denied), "refusals": checked,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, default=PACKET)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        with TemporaryDirectory(prefix="KitMeasuredEq") as directory:
            request = json.load(sys.stdin)
            name = request["document"]["metadata"]["name"]
            row = worker(request, Path(directory).resolve() / (name + ".SLDPRT"))
            print(json.dumps(row, sort_keys=True, allow_nan=False))
        return
    request = json.dumps(disclosed(args.packet), allow_nan=False)
    rows = []
    for _ in range(2):
        output = run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=request, text=True,
                     capture_output=True, timeout=90, check=False)
        require(output.returncode == 0 and not output.stderr, output.stderr)
        rows.append(json.loads(output.stdout))
    require(rows[0] == rows[1] and rows[0]["runtime_reads"] == 0, "fresh construction workers disagree")
    print(json.dumps({
        "schema": "kit.sw2026.public-width-depth-writer.v2",
        "native_result_sha256": NATIVE,
        "release_receipt_sha256": RECEIPT_SHA,
        "method_sha256": digest(HERE.read_bytes()),
        "neutral_input_sha256": NEUTRAL,
        "heldout_inputs_read": 0,
        "native_processes_started": 0,
        "isolated_worker_processes": len(rows),
        "exact_native_tested_output": rows[0],
    }, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
