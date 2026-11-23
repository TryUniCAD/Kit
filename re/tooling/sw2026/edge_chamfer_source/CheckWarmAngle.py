from argparse import ArgumentParser
from dataclasses import replace
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parent), str(HERE.parent / "distance_pair")]

from CheckMeasuredAngle import BASE, EPOCH, FORMAT, MEASURE, NATIVE, RESULT, TRIAL, canonical, digest, locked, reject, writer
from CheckMeasuredPair import warm_modules
from ChamferModel import compare_six, predict, values_si
from ProvePublicChamferRead import selected_witnesses, xyz
from ProveWarmPairRead import metrics, read_doc
from VerifySdkCircleEndRegistration import OutputGuard
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import NativePartModel, SldprtAdapter
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import ReadChmfOwn
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.ReadWarmChmf import ReadWarmChmf
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.Features.FeatureKinds import ChamferFeature
from interchange.Features.ScopedExtrude import ScopedExtrude
from interchange.geometry.Models.Selection import SelectPathElem


SOURCE = "a696a97d73129ef7ffd7e829dfff7d1729000309e1273c0bef70b5f2ceedddb8"
ARCHIVE = "7be3756016025093a917c74bc1b2480da140e2d19d1eab67f7c55c53f23f602e"
SPEC = "ef23dfb43314e133f7b6d490a8c257208244c3163c50659bac7bae9d7a6e4bc4"


def shape(full, proof, case, branch, edited):
    body, = full.bodies
    boundary = full.brep
    assert boundary is not None and not boundary.validate(frozenset((body.id,)))
    actual = replace(boundary, bodies=(replace(boundary.bodies[0], design_body_id=""),))
    assert actual == proof.BrepValue and boundary.bodies[0].design_body_id == body.id
    selected, = (row for row in full.brep_payloads if row.id == body.attributes["parasolid_active_payload_id"])
    assert selected.sha256 == proof.PayloadHash
    expected = predict(case, values_si(case, edited), tuple(branch))
    topo = body.topology
    assert (topo.solid_count, topo.shell_count, topo.face_count, topo.edge_count, topo.vertex_count) == (1, 1, 7, 15, 10)
    assert sorted(tuple(round(value * 0.001, 12) for value in xyz(row.point)) for row in boundary.vertices) == sorted(
        tuple(round(value, 12) for value in point) for point in expected["vertices"]
    )
    measured = (topo.volume * 1e-9, metrics(ReadMassRings(boundary)) * 1e-6,
                *(value * 0.001 for value in body.attributes["solidworks.body_centroid_mm"]))
    desired = (expected["volume"], expected["area"], *expected["com"])
    assert all(compare_six(value, wanted, 1e-12)[2] for value, wanted in zip(measured, desired, strict=True))
    return {"physical_slots": [proof.BodySlot, proof.EdgeSlot, proof.FaceSlot],
            "mark_ids": proof.MarkIds, "matches_stored_brep": True, "active_payload_sha256": proof.PayloadHash,
            "numerical_checks": len(measured), "volume_m3": measured[0], "area_m2": measured[1], "centroid_m": measured[2:]}


def history(full, design, case, branch, evidence):
    assert full.feature_timeline == design.feature_timeline and full.parameters == design.parameters
    assert full.sketches == design.sketches and full.selections == design.selections and design.brep is None
    (feature,) = tuple(row for row in full.feature_timeline if row.kind == "chamfer")
    stock = next(row for row in full.feature_timeline if row.id == feature.input_feature_ids[0])
    assert isinstance(stock.definition, ScopedExtrude) and stock.definition.ScopeMode == "first_creator"
    assert isinstance(feature.definition, ChamferFeature) and feature.definition.mode == "distance_angle"
    assert full.bodies[0].final_feature_id == feature.id and full.bodies[0].name == feature.name
    assert full.bodies[0].attributes["native_object_id"] == 35
    drivers = tuple(row for row in full.parameters if row.owner_id == feature.id)
    assert tuple(row.id for row in drivers) == feature.parameter_ids
    for index, (driver, expected) in enumerate(zip(drivers, evidence["drivers"], strict=True)):
        assert driver.name == expected["name"] and driver.attributes["persistent_dimension_id"] == expected["dimension_id"]
        assert driver.role == "driving" and driver.value.unit == ("mm" if index == 0 else "rad")
        assert driver.value.value == expected["value_si"] * (1000 if index == 0 else 1)
        (source,) = driver.provenance.spans
        wire = expected["owners"][-1]
        assert (source.stream, source.offset, source.length) == (wire["stream"], wire["offset"], wire["end"] - wire["offset"])
    assert (feature.definition.distance, feature.definition.angle) == tuple(row.value for row in drivers)
    picks = tuple(next(row for row in full.selections if row.id == key) for key in feature.selection_ids)
    roles = ("edge", "distance face")
    assert tuple(row.path for row in picks) == tuple((SelectPathElem("feature", stock.id, role),) for role in roles)
    assert all(max(abs(a - b) for a, b in zip(xyz(item.point), expected, strict=True)) <= 1e-8
               for item, expected in zip(picks, selected_witnesses(case, branch), strict=True))
    return {"parameter_names": [row.name for row in drivers], "driver_ids": [row.attributes["persistent_dimension_id"] for row in drivers],
            "effective_si_values": [row["value_si"] for row in evidence["drivers"]], "tree_rows": len(full.feature_timeline),
            "owned_selection_order": roles}


def prove(request, data):
    row, case, branch, edited = (request[name] for name in ("archive_evidence", "case", "branch", "edited"))
    assert digest(data) == row["source_sha256"]
    archive = SldprtArchive.from_bytes(data)
    graph = ReadNativeLink(archive, 0, ReadChamfers=True)
    model = NativePartModel(archive, "Default", StrictRefs=True)
    owners = ReadChmfOwn(graph, AllowDistancePair=True)
    proof = ReadWarmChmf(archive, model, graph).WarmValue
    assert proof is not None
    assert [proof.BodySlot, proof.EdgeSlot, proof.FaceSlot] == [
        row["physical"]["body_slot"], row["physical"]["stock_support"]["edge_slot"], row["physical"]["result_face_slot"]
    ]
    assert tuple(proof.MarkIds) == tuple(item["mark"] for item in row["physical"]["kernel_stages"])
    feature = next(value for value in model.features if value.object_id == owners.FeatureValue.FieldsValue["f08"])
    assert len(feature.dimensions) == 2
    dist_dim = next(value for value in feature.dimensions if value.name == "D1")
    angle_dim = next(value for value in feature.dimensions if value.name == "D2")
    def change_rows(dimensions):
        replacement = replace(feature, dimensions=dimensions)
        return replace(model, features=tuple(replacement if value is feature else value for value in model.features))
    reject(lambda: ReadWarmChmf(archive, change_rows((dist_dim, dist_dim)), graph), "missing or duplicate display roles")
    reject(lambda: ReadWarmChmf(archive, change_rows((dist_dim, replace(angle_dim, kind="distance"))), graph), "display kinds differ")
    full, design = read_doc(data, True), read_doc(data, False)
    for include, expected in ((True, full), (False, design)):
        direct = SldprtAdapter().read(BytesIO(data), ReadOptions(include_brep=include, configuration="Default"))
        assert direct.to_json(indent=None) == expected.to_json(indent=None)
        assert direct.metadata["solidworks.typed_resolved_semantics"]["status"] == "supplemented_saved_angle_chamfer"
    options = request["write_options"]
    sink = BytesIO(b"retained")
    assert not any(SldprtWriter().supports(doc, sink) for doc in (full, design))
    reject(lambda: writer(full, sink, options), "requires the exact passing SOLIDWORKS")
    reject(lambda: writer(design, sink, options), "native-only feature definitions cannot be exported")
    assert sink.getvalue() == b"retained" and sink.tell() == 0
    return {"case": case["name"], "edited": edited, "source_sha256": row["source_sha256"],
            "keyword_order": [value.name for value in feature.dimensions],
            "native_source_phase_sha256": row["native_phase_sha256"],
            "history": history(full, design, case, branch, row), "shape": shape(full, proof, case, branch, edited),
            "reader_routes": 4, "foreign_display_refusals": 2, "saved_publication_refused": True}


def worker(request):
    data = bytes.fromhex(request["payload"])
    warm_modules()
    with TemporaryDirectory(prefix="KitWarmAngle.") as temporary:
        audit = OutputGuard(Path(temporary), "unexpected")
        sys.addaudithook(audit.audit)
        with audit.active("memory"):
            report = prove(request, data)
    assert not audit.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules)
    return report | {"runtime_accesses": len(audit.denied)}


def supervise(source, output):
    receipt = locked(RESULT / "EdgeChamferDisclosedSource01.json", SOURCE)
    archive = locked(RESULT / "EdgeChamferTypedArchiveRead01.json", ARCHIVE)
    spec_bytes = HERE.with_name("DisclosedChamferInputs.json").read_bytes()
    assert digest(spec_bytes) == SPEC
    spec = loads(spec_bytes)
    assert receipt["passed"] and receipt["distinct_processes"] == 8 and archive["disclosed_lock_sha256"] == SOURCE
    assert all(value["passed"] for value in receipt["controls"].values())
    trial = locked(RESULT / "ChamferSignedSideTrial01.json", TRIAL)
    native = locked(RESULT / "ChamferSignedSideNative01.json", NATIVE)
    options = {"final_destination": trial["cases"][0]["locator"], MEASURE: {
        "written_at": EPOCH, "receipt": {"trial": trial, "native_result": native},
    }}
    result = []
    for case, authority in zip(spec["cases"], receipt["sources"], strict=True):
        for edited, role in ((False, "original"), (True, "edited")):
            row, = (value for value in archive["disclosed_parts"] if (value["case"], value["edited"]) == (case["name"], edited))
            assert authority[role + "_sha256"] == row["source_sha256"]
            file = source / (case["name"] + ("Edited" if edited else "") + ".SLDPRT")
            payload = file.read_bytes()
            assert digest(payload) == row["source_sha256"]
            request = {"case": case, "branch": authority["orientation"], "archive_evidence": row,
                       "edited": edited, "payload": payload.hex(), "write_options": options}
            measured = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=dumps(request), capture_output=True,
                           text=True, timeout=90, check=False)
            assert measured.returncode == 0 and not measured.stderr, measured.stderr
            result.append(loads(measured.stdout))
    root = HERE.parents[4]
    names = ("BindChmfModel.py", "BindChmfRoots.py", "Warm/OrderWarmDims.py", "Warm/ReadWarmChmf.py")
    sources = tuple(root / "src/convert/adapters/solidworks/Core/TypedResolved/Chamfers" / name for name in names)
    report = {"schema": "kit.sw2026.saved-angle-chamfer-sdk.v1", "base": BASE,
              "disclosed_lock_sha256": SOURCE, "archive_proof_sha256": ARCHIVE, "spec_sha256": SPEC,
              "new_native_processes": 0, "new_heldout_credit": 0, "guarded_workers": len(result),
              "method_sha256": digest(HERE.read_bytes()), "cases": result,
              "source_sha256": {path.relative_to(root).as_posix(): digest(path.read_bytes()) for path in sources}}
    with output.open("xb") as stream:
        stream.write(canonical(report))
    print(digest(output.read_bytes()))


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        print(dumps(worker(loads(sys.stdin.read()))))
    else:
        parser = ArgumentParser()
        parser.add_argument("--source", type=Path, required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args()
        supervise(args.source, args.output)
