from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from struct import pack
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / "src"))

from convert import open_document, write_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream, KPartFormatId
from convert.adapters.solidworks.Core.Adapter import NativePartModel, SldprtAdapter
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.Partition.PartTopology import LinearPartBox
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import ReadChmfOwn
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import EdgeChmfRows
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.ReadWarmChmf import ReadWarmChmf
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.Geometry.Parasolid import DecodePartData
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.Features.ScopedExtrude import ScopedExtrude

from math import isclose, sqrt
from ObservePairArchives import guard

ARCHIVE_PIN = "89386f4bac8f4619bb4d37efdb1fb87cd0f52877caad193d08a323baa722178f"
SELECTOR_PIN = "a1bdd5b12a650a36b17896cb78d287a701e2df3930c85ab038716feec26311b6"
NAMES = ("EqualOriginal", "EqualEdited", "UnequalOriginal", "UnequalEdited")
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
BASE = "64a0b5947f5d71f7f1378f1a6fee12394efc959f"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def pinned(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, f"unexpected disclosed source or evidence hash for {path.name}")
    return data


def read_doc(data, full=True):
    return open_document(BytesIO(data), source_format=KPartFormatId, include_brep=full, strict=True)


def refuse(action, expected):
    try:
        action()
    except ValueError as error:
        require(expected in str(error), f"wrong refusal for {expected!r}: {error}")
        return str(error)
    raise ValueError(f"missing refusal for {expected!r}")


@contextmanager
def altered(fields, key, new):
    original = fields[key]
    fields[key] = new
    try:
        yield
    finally:
        fields[key] = original


def metrics(rings):
    area = 0.0
    for ring in rings:
        anchor = ring[0]
        for previous, current in zip(ring[1:-1], ring[2:], strict=True):
            double = CrossVector(OffsetVector(previous, anchor, -1), OffsetVector(current, anchor, -1))
            area += sqrt(DotVector(double, double)) / 2
    return area


def expected_metric(first, other):
    low = (-21.375, -30.875, 0.0)
    high = (43.875, 14.625, 18.75)
    width, height, depth = (b - a for a, b in zip(low, high, strict=True))
    rectangle = width * height
    removed = first * other / 2
    polygon = rectangle - removed
    area = 2 * polygon + (2 * (width + height) - first - other + sqrt(first * first + other * other)) * depth
    centroid = ((rectangle * (high[0] + low[0]) / 2 - removed * (high[0] - first / 3)) / polygon,
                (rectangle * (high[1] + low[1]) / 2 - removed * (high[1] - other / 3)) / polygon,
                depth / 2)
    return (low, high), polygon * depth, area, centroid


def coords(vector):
    return vector.x, vector.y, vector.z


def positive(document, sem, model, owners, proof, source, row):
    require(document.feature_timeline == sem.feature_timeline and document.parameters == sem.parameters
            and document.sketches == sem.sketches and document.selections == sem.selections
            and sem.brep is None and not sem.brep_payloads, "semantic-only route differs or leaks geometry")
    (config,) = document.configurations
    require(config.name == "Default" and config.active, "physical default configuration lost")
    sketch, stock, chamfer = document.feature_timeline[-3:]
    (line_sketch,) = document.sketches
    tree_checks = {
        "support_rows": len(document.feature_timeline) == 27
        and any(step.name == "Exploded Views 19" for step in document.feature_timeline)
        and tuple((step.id, step.name) for step in document.feature_timeline)
        == tuple((f"sldprt:feature:{feature.object_id}", feature.name) for feature in model.features),
        "stock_profile": sketch.sketch_id == line_sketch.id
        and stock.input_feature_ids == (sketch.id,) and stock.sketch_id == line_sketch.id,
        "live_lines_relations": len(line_sketch.entities) == 4 and len(line_sketch.constraints) == 4,
        "creation_scope": stock.operation.value == "create" and isinstance(stock.definition, ScopedExtrude)
        and stock.definition.ScopeMode == "first_creator",
        "modifier": chamfer.input_feature_ids == (stock.id,) and len(chamfer.selection_ids) == 2,
        "read_diagnostics": not document.diagnostics,
    }
    require(all(tree_checks.values()), f"strict saved graph lost owners: {tree_checks}; {document.diagnostics}")
    wanted = tuple((item["name"], item["persistent_id"], item["value_si"] * 1000)
                   for item in row["drivers"].values())
    params = tuple(p for p in document.parameters if p.owner_id == chamfer.id)
    require(tuple((p.name, p.attributes["persistent_dimension_id"], p.value.value) for p in params) == wanted
            and tuple(p.id for p in params) == chamfer.parameter_ids, "driver identity, value or order differs")
    mode = "equal_distance" if row["mode_word"] == 18 else "two_distances"
    require(chamfer.definition.mode == mode and chamfer.definition.distance == params[0].value
            and chamfer.definition.second_distance == (params[1].value if mode == "two_distances" else None),
            "public typed chamfer lost its actual distance mode")
    picks = tuple(next(selection for selection in document.selections if selection.id == name)
                  for name in chamfer.selection_ids)
    require(all(pick.path[0].entity_id == stock.id and pick.provenance is not None for pick in picks)
            and tuple(coords(pick.point) for pick in picks) == ((43.875, 14.625, 9.375), (11.25, 14.625, 9.375)),
            "portable selection did not retain the actual stock edge and carrier")
    (body,) = document.bodies
    require(body.name == chamfer.name and body.final_feature_id == chamfer.id and body.provenance == chamfer.provenance
            and body.attributes["native_object_id"] == owners.FeatureValue.FieldsValue["f08"],
            "physical body did not retain its sole actual modifier")
    actual = replace(document.brep, bodies=(replace(document.brep.bodies[0], design_body_id=""),))
    require(actual == proof.BrepValue and document.brep.bodies[0].design_body_id == body.id
            and source.sha256 == proof.PayloadHash, "default reader replaced the saved geometry instead of binding it")
    (payload,) = (value for value in document.brep_payloads if value.id == body.attributes["parasolid_active_payload_id"])
    require(payload.sha256 == source.sha256 and payload.source_stream == KPartitionStream and payload.data == source.data,
            "body no longer points to its exact selected active archive frame")
    topology = body.topology
    require((topology.solid_count, topology.shell_count, topology.face_count, topology.edge_count, topology.vertex_count)
            == (1, 1, 7, 15, 10), "unexpected owned body topology")
    bounds = LinearPartBox(document.brep)
    target_bounds, volume, area, centroid = expected_metric(params[-1].value.value, params[0].value.value)
    observed = (topology.volume, metrics(ReadMassRings(document.brep)), *body.attributes["solidworks.body_centroid_mm"])
    require(bounds == topology.bounding_box and all(
        isclose(value, target, rel_tol=1e-8, abs_tol=1e-8)
        for xyz, expected in zip((bounds.minimum, bounds.maximum), target_bounds, strict=True)
        for value, target in zip(coords(xyz), expected, strict=True))
        and all(isclose(value, target, rel_tol=1e-8, abs_tol=1e-8)
                for value, target in zip(observed, (volume, area, *centroid), strict=True)),
        f"saved mass geometry differs: {observed}, {(volume, area, *centroid)}, {bounds}, {topology.bounding_box}")
    return {"metrics_mm": observed, "placed_bounds_mm": target_bounds, "mode": mode,
            "parameters_name_id_mm": wanted, "tree_rows": len(document.feature_timeline),
            "sketch_lines": len(line_sketch.entities), "sketch_constraints": len(line_sketch.constraints),
            "physical_body_slot": proof.BodySlot, "restored_edge_slot": proof.EdgeSlot,
            "bevel_face_slot": proof.FaceSlot, "mark_ids": proof.MarkIds,
            "active_payload_sha256": proof.PayloadHash, "topology": [1, 1, 7, 15, 10]}


def rewrap(archive, partition, *, include=True):
    streams = dict(archive.streams)
    if include:
        streams[KPartitionStream] = partition
    else:
        del streams[KPartitionStream]
    return BuildSldprt(streams, FormatVersion=archive.format_version)


def negatives(archive, document, model, link, owners, foreign):
    feature = owners.FeatureValue.FieldsValue
    stock, chamfer = document.feature_timeline[-2:]
    checks = {}
    wrong_tail = replace(chamfer, input_feature_ids=stock.input_feature_ids)
    wrong_doc = replace(document, feature_timeline=(*document.feature_timeline[:-1], wrong_tail))
    checks["non_owner_chamfer"] = refuse(wrong_doc.assert_valid, "first creator scope requires one active root solid extrusion")
    missing = rewrap(archive, b"", include=False)
    checks["absent_partition"] = refuse(lambda:read_doc(missing), "saved distance chamfer ownership rejected")
    checks["absent_partition_metadata_only"] = refuse(lambda:read_doc(missing, False), "saved distance chamfer ownership rejected")
    crossed = rewrap(archive, SldprtArchive.from_bytes(foreign).require(KPartitionStream))
    checks["foreign_live_owner"] = refuse(lambda:read_doc(crossed), "foreign to the recorded modifier")
    raw = SldprtAdapter().read(BytesIO(crossed), ReadOptions(strict=True, extract_raw_brep=True))
    expected = DecodePartData(SldprtArchive.from_bytes(foreign).require(KPartitionStream), KPartitionStream)
    require(tuple((value.kind, value.sha256) for value in raw.brep_payloads if value.source_stream == KPartitionStream)
            == tuple((value.kind, value.sha256) for value in expected),
            "ordinary raw extraction did not retain the exact independent partition and delta frames")
    selected = feature["f880"]["ff0"]["items"][0]
    historical = EdgeChmfRows(owners.SelectedRef)[0].FieldsValue["f10"]["f10"].FieldsValue["f08"]
    with altered(selected, "o", owners.DetachedRef):
        checks["crossed_keeper"] = refuse(lambda:ReadWarmChmf(archive, model, link), "conflicting selected edge")
    with altered(historical.FieldsValue["shared"]["h18"].FieldsValue, "f08", "foreign.SLDPRT"):
        checks["foreign_historical_self"] = refuse(lambda:ReadWarmChmf(archive, model, link), "differs from its actual local headers")
    driver = owners.Distance
    new_length = driver.ValueSi + 0.001
    with altered(driver.ParameterNode.FieldsValue, "f58", new_length), altered(
            driver.DisplayNode.FieldsValue["f5b0"], "data", pack("<d", new_length)):
        checks["matching_driver_but_stale_solid"] = refuse(lambda:ReadWarmChmf(archive, model, link), "outward boundary differs")
    active_mark = owners.Controllers[-1].FieldsValue
    with altered(active_mark, "f18", active_mark["f18"] + 1):
        checks["foreign_mark"] = refuse(lambda:ReadWarmChmf(archive, model, link), "differs from its actual controller")
    output = BytesIO()
    reason = "native-only feature definitions cannot be exported"
    refuse(lambda:write_document(document, output, destination_format=KPartFormatId, allow_carrier=False), reason)
    checks["refused_native_publication"] = reason
    require(not output.getvalue(), "unqualified saved history published output")
    return checks


def worker():
    packet = loads(sys.stdin.buffer.read())
    data, foreign = bytes.fromhex(packet["source"]), bytes.fromhex(packet["foreign"])
    row = packet["row"]
    require(digest(data) == row["source_sha256"] and digest(foreign) == packet["foreign_sha256"],
            "worker source changed in transport")
    denied = start_guard()
    archive = SldprtArchive.from_bytes(data)
    model = NativePartModel(archive, None)
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    owners = ReadChmfOwn(link, AllowDistancePair=True)
    shape = ReadWarmChmf(archive, model, link)
    require(shape.WarmValue is not None, "physical warm proof missing")
    require([list((value.ClassValue.NameValue, value.FieldsValue["f38"], value.FieldsValue.get("f3c"))) for value in EdgeChmfRows(owners.SelectedRef)]
            == packet["selectors"]["ordered_edge_roles"], "actual typed selector order differs from disclosed evidence")
    active, delta = DecodePartData(archive.require(KPartitionStream), KPartitionStream)
    require(digest(active.data) == active.sha256 and digest(delta.data) == delta.sha256, "physical wrapper digest mismatch")
    document, sem = read_doc(data), read_doc(data, False)
    direct = SldprtAdapter().read(BytesIO(data), ReadOptions(strict=True))
    require(direct == document, "ordinary registry and direct adapter disagree")
    report = positive(document, sem, model, owners, shape.WarmValue, active, row)
    faults = negatives(archive, document, model, link, owners, foreign)
    require(not denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
            "saved reader accessed an external resource or CAD")
    print(dumps(report | {"case": packet["name"], "source_sha256": digest(data), "history_payload_sha256": delta.sha256,
                         "native_terminal_sha256": row["native_terminal_sha256"], "refusals": faults, "guarded_input_reads": len(denied)},
                sort_keys=True))


def start_guard():
    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    lookup("utf-8-sig")
    return guard()


def cold_worker():
    from ProvePairRead import authored, prepare

    request = loads(sys.stdin.buffer.read())
    neutral = authored(request["case"], request["side"])
    denied = start_guard()
    raw = prepare(neutral, request["locator"], request["epoch"], False).BytesValue
    require(digest(raw) == request["archive_sha256"], "signed generated control archive changed")
    current = [digest(dumps(read_doc(raw, full).to_dict(), sort_keys=True, separators=(",", ":")).encode())
               for full in (False, True)]
    require(current == request["baseline_docs"] and not denied, "signed cold control readback changed")
    print(dumps({"archive_sha256": digest(raw), "baseline_document_hashes": current,
                 "guarded_input_reads": len(denied)}, sort_keys=True))


def signed_checks(args):
    from ProvePairRead import EPOCH, SIGNED_DOCS, TRIAL_SHA

    trial = loads(pinned(args.signed_trial, TRIAL_SHA))
    controls = []
    for index, (case, row, docs) in enumerate(zip(trial["spec"]["cases"], trial["cases"], SIGNED_DOCS, strict=True)):
        request = {"case": case, "archive_sha256": row["archive_sha256"], "baseline_docs": docs,
                   "locator": row["locator"], "epoch": EPOCH + index * 61, "side": row["branch"][0]}
        child = run((sys.executable, "-E", "-B", str(HERE), "--cold-worker"), input=dumps(request).encode(),
                    capture_output=True, check=False, cwd=ROOT, timeout=60)
        require(child.returncode == 0 and not child.stderr, child.stderr.decode())
        controls.append(loads(child.stdout))
    return {"trial_sha256": TRIAL_SHA, "controls": controls}


def supervise(args):
    observed = loads(pinned(MEASUREMENTS / "ChamferDistancePairArchive01.json", ARCHIVE_PIN))["cases"]
    selectors = loads(pinned(MEASUREMENTS / "ChamferDistancePairSelectors01.json", SELECTOR_PIN))["cases"]
    sources = tuple(pinned(args.folder / f"{name}.SLDPRT", row["source_sha256"])
                    for name, row in zip(NAMES, observed, strict=True))
    reports = []
    for index, (name, source, row, roles) in enumerate(zip(NAMES, sources, observed, selectors, strict=True)):
        require(row["source_sha256"] == roles["source_sha256"], "selection and stream receipts disagree")
        foreign = (index + 2) % 4
        packet = {"name": name, "source": source.hex(), "foreign": sources[foreign].hex(),
                  "foreign_sha256": observed[foreign]["source_sha256"], "row": row, "selectors": roles}
        child = run((sys.executable, "-E", "-B", str(HERE), "--worker"), input=dumps(packet).encode(),
                    capture_output=True, check=False, cwd=ROOT, timeout=60)
        require(child.returncode == 0, child.stderr.decode())
        reports.append(loads(child.stdout))
    paths = {
        "src/convert/adapters/solidworks/Core/Adapter.py",
        "src/interchange/document/Validation/FirstScopeErrs.py",
        "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/SavedScope/CheckSavedFaces.py",
        *(str(path.relative_to(ROOT)) for path in
          (ROOT / "src/convert/adapters/solidworks/Core/TypedResolved/Chamfers").rglob("*.py")),
    }
    signed = signed_checks(args)
    details = {
        "signed_cold_model_controls": signed,
        "schema": "kit-disclosed-saved-distance-chamfer-read/1",
        "base_revision": BASE,
        "archive_receipt_sha256": ARCHIVE_PIN,
        "selector_receipt_sha256": SELECTOR_PIN,
        "guarded_processes": len(reports) + len(signed["controls"]),
        "guarded_input_reads": sum(row["guarded_input_reads"] for row in (*reports, *signed["controls"])),
        "reader_sha256": {path: digest((ROOT / path).read_bytes()) for path in sorted(paths)},
        "proof_sha256": digest(HERE.read_bytes()),
        "proof_dependencies_sha256": {
            str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in (
                HERE.with_name("ObservePairArchives.py"), HERE.with_name("ProvePairRead.py"),
                HERE.parents[1] / "ProvePublicChamferWrite.py",
            )
        },
        "new_native_processes": 0,
        "held_out_sources_read": 0,
        "whole_source_transfer_admitted": False,
        "cases": reports,
    }
    with args.report.open("x", encoding="utf-8", newline="\n") as output:
        output.write(dumps(details, indent=2, sort_keys=True) + "\n")
    print(f"{len(reports)} guarded disclosed warm reads passed")


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--cold-worker", action="store_true")
    parser.add_argument("--signed-trial", type=Path)
    parser.add_argument("--folder", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker()
    elif args.cold_worker:
        cold_worker()
    else:
        require(args.folder is not None and args.signed_trial is not None and args.report is not None,
                "--folder, --signed-trial and fresh --report are required")
        supervise(args)


if __name__ == "__main__":
    main()
