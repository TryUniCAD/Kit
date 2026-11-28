from argparse import ArgumentParser
from dataclasses import replace
from importlib import import_module
import json
from math import dist, isclose, pi
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent),
                str(ROOT / "re/tooling/sw2026/revolve/PrincipalReader")]
from AuditFilletArchive import DISCLOSED_LOCK, checked, input_custody, observe_native, require
from AuditPrincipalReader import make_guard
from FilletModel import predict, validate_cases
from convert import open_document
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletHist import ReadFilletHist
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletBrep import BindFilletBrep
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletDoc import BindFilletDoc
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.JoinFilletEdge import JoinFilletEdge
from interchange.brep.Curves.BrepCurves import CircleCurve

FORMAT = "solidworks.sldprt"
STATUS = "solidworks.typed_saved_edge_fillet"


def close(actual, expected, near_zero=1e-12):
    require((abs(actual) < near_zero and abs(expected) < near_zero) or format(actual, ".6g") == format(expected, ".6g"),
            "SDK geometry differs from independent native measurements")


def refuses(action, diagnostic):
    try:
        action()
    except (ValueError, KeyError) as error:
        require(diagnostic in str(error), "unexpected alternate owner refusal: " + str(error))
        return
    raise ValueError("an alternate owner was accepted")


def contrasts(legacy, history, top, unrelated, archive):
    edge = JoinFilletEdge(history, top)
    ref, archive_fields = edge.RefValue, history.DriveValue.ItemValue.FieldsValue
    driver = archive_fields["f10"]
    selected = driver.FieldsValue["fe8"]
    try:
        driver.FieldsValue["fe8"] = None
        refuses(lambda: JoinFilletEdge(history, top), "keeper do not own the actual selected edge")
    finally:
        driver.FieldsValue["fe8"] = selected
    first, second, *_ = ref.FieldsValue["f10"]
    first, second = first["f08"], second["f08"]
    ordinal = first.FieldsValue["f38"]
    try:
        first.FieldsValue["f38"] = second.FieldsValue["f38"]
        refuses(lambda: JoinFilletEdge(history, top), "different stock face roles")
    finally:
        first.FieldsValue["f38"] = ordinal
    live = history.StagesValue[0]
    rim = next(row for row in live.NodesValue.values() if row.KindValue == 31 and row.String("sense") == "-")
    changed = replace(rim, FieldsValue={**rim.FieldsValue, "sense": "+"})
    fake = replace(history, StagesValue=(replace(live, NodesValue={**live.NodesValue, rim.IndexValue: changed}),
                                         *history.StagesValue[1:]))
    refuses(lambda: BindFilletBrep(fake, legacy.brep, legacy.bodies[0].id), "quarter round")
    refuses(lambda: BindFilletDoc(unrelated, archive), "public shape differs")
    return ["crossed_radial_alias", "duplicate_stock_face", "opposite_circle_sense", "foreign_decoded_shape"]


def warm():
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        from codecs import lookup
        lookup(codec)
    for name in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                 "interchange.document.Models.DocumentProvenance", "interchange.document.Models.DocumentWalk",
                 "interchange.document.Validation.DocumentValidate", "interchange.document.Validation.DocumentAssemblyValidate",
                 "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
                 "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.PlaneRevValidate",
                 "interchange.document.Validation.DistExtValidate"):
        import_module(name)


def worker(request):
    raw = checked(Path(request["path"]), request["digest"])
    other = request.get("contrast")
    if other:
        foreign = checked(Path(other["path"]), other["digest"])
    warm()
    state, audit = make_guard(ROOT / "src")
    state["enabled"] = True
    report = open_document(raw, source_format=FORMAT, strict=True, include_tessellation=False)
    history_view = open_document(raw, source_format=FORMAT, strict=True, include_brep=False)
    require(report.metadata.get(STATUS) is True and STATUS not in history_view.metadata
            and history_view.brep is None and not history_view.brep_payloads, "warm proof changed the other reader views")
    body, = report.bodies
    owner, = [value for value in report.feature_timeline if value.id == body.final_feature_id]
    driver, = [value for value in report.parameters if value.owner_id == owner.id]
    pick, = [value for value in report.selections if value.id in owner.selection_ids]
    expected = request["expected"]
    original = request["stock_depth"]
    closed = report.brep
    require(body.name == owner.name == expected["fillet_name"] and closed is not None
            and closed.bodies[0].design_body_id == body.id and not closed.validate(frozenset({body.id}))
            and body.provenance == owner.provenance and driver.provenance and pick.provenance
            and driver.name == "D1" and driver.role == "driving" and driver.value == owner.definition.radius,
            "public read lost the actual warm body or driving owner")
    require(len(report.sketches) == len(history_view.sketches) == 1
            and tuple(v.id for v in report.feature_timeline) == tuple(v.id for v in history_view.feature_timeline)
            and any(p.owner_id == owner.input_feature_ids[0] and isclose(p.value.value / 1000.0, original)
                    for p in report.parameters), "warm read changed stock D1 or recursive history identities")
    near = lambda a, b: dist(a, b) < 1e-10
    observed_ends = sorted(tuple(v / 1000.0 for v in point) for point in pick.attributes["native_edge_endpoints_mm"])
    require(all(near(a, b) for a, b in zip(observed_ends, expected["edge_endpoints_m"], strict=True)),
            "public selection does not name the actual old stock edge")
    radii = expected["radius_m"]
    require(isclose(driver.value.value / 1000.0, radii, rel_tol=1e-14), "actual D1 differs")
    topology = body.topology
    counts = {kind: len(getattr(closed, kind)) for kind in ("faces", "edges", "vertices")}
    require(counts == expected["body_counts"] and
            (topology.face_count, topology.edge_count, topology.vertex_count) == tuple(counts.values()),
            "public rounded topology differs from native")
    oracle = expected["volume_area_centroid_si"]
    close(topology.volume / 1e9, oracle["volume"])
    close(topology.surface_area / 1e6, oracle["area"])
    for actual, desired in zip(body.attributes["solidworks.body_centroid_mm"], oracle["centroid"], strict=True):
        close(actual / 1000, desired)
    curves = {curve.id: curve for curve in closed.curves if isinstance(curve, CircleCurve)}
    arcs = [edge for edge in closed.edges if edge.curve_id in curves]
    require(len(arcs) == 2 and all(isclose(edge.end_parameter - edge.start_parameter, pi / 2, rel_tol=1e-12)
            for edge in arcs), "actual warm fillet requires two quarter arcs")
    negatives = []
    if other:
        archive = SldprtArchive.from_bytes(raw)
        history = ReadFilletHist(archive)
        top = ReadHeaderGraph(archive.require("Header2"), 19000)
        legacy = replace(report, brep=replace(report.brep, curves=tuple(
            replace(c, axis=type(c.axis)(-c.axis.x, -c.axis.y, -c.axis.z))
            if isinstance(c, CircleCurve) and c.attributes["parasolid.curve_sense"] == "-" else c
            for c in report.brep.curves
        )))
        unrelated = open_document(foreign, source_format=FORMAT, strict=True, include_tessellation=False)
        negatives = contrasts(legacy, history, top, unrelated, archive)
    require(not audit["unexpected_attempts"] and not any(k.startswith(("pythoncom", "win32com")) for k in sys.modules),
            "saved read attempted external access or CAD automation")
    return {"source_sha256": request["digest"], "typed_edge_slot": pick.attributes["native_previous_edge"],
            "body_counts": counts, "native_numeric_comparisons": 5, "round_spans_radians": [edge.end_parameter - edge.start_parameter for edge in arcs],
            "curve_senses": sorted(c.attributes["parasolid.curve_sense"] for c in curves.values()),
            "guarded_package_grammar_reads": audit["grammar_reads"], "unexpected_external_access_attempts": 0,
            "history_only_unchanged": True, "refusals": negatives}


def compare(capture):
    lock, constants, inputs = input_custody(capture)
    definitions = validate_cases(json.loads((HERE.parent / "DisclosedFilletInputs.json").read_bytes()))
    results = []
    for slot, (definition, (name, row, rows)) in enumerate(zip(definitions, inputs, strict=True)):
        for edited in (False, True):
            stem = name + ("Edited" if edited else "")
            observed = rows[2 if edited else 1]["reopened"]
            request = {"path": str(capture / name / (stem + ".SLDPRT")),
                       "digest": row["edited_sha256" if edited else "original_sha256"],
                       "expected": observe_native(definition, observed, edited, constants),
                       "stock_depth": definition["size_mm"][2] / 1000.0}
            if slot == 0 and not edited:
                other, source, _ = inputs[1]
                request["contrast"] = {"path": str(capture / other / (other + ".SLDPRT")),
                                       "digest": source["original_sha256"]}
            launch = subprocess.run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                                    input=json.dumps(request), capture_output=True, text=True, timeout=90)
            require(launch.returncode == 0 and not launch.stderr, launch.stderr)
            results.append(json.loads(launch.stdout) | {"case": name, "edited": edited})
    return {"schema": "kit.sw2026.saved-edge-fillet-sdk-read.v1", "source_lock_sha256": DISCLOSED_LOCK,
            "guarded_processes": len(results), "native_launches": 0, "heldout_credit": 0, "results": results}


def observed_axial(path):
    receipt_path = ROOT / "re/solidworks/measurements/2026/EdgeFilletModelNative01.json"
    receipt_pin = "ed4b234a0e8b922d5a3a379277525665e701cbfa5fc69067838f1e7894e2eb79"
    receipt = json.loads(checked(receipt_path, receipt_pin))
    phase = receipt["cases"]["EdgeFilletAxial"]["phases"]["reopen-edit-save"]
    require(receipt["comparison_valid"] and not receipt["passed"] and phase["save_status"] == [True, 0, 0]
            and phase["checks"] == phase["checks_passed"] == 45,
            "exact axial evidence lacks its clean save before the native lifetime failure")
    acquired = phase["states"]["edited"]
    volume, area, centre = acquired["volume_area_centroid"]
    spec = validate_cases(json.loads((HERE.parent / "DisclosedFilletInputs.json").read_bytes()))
    case = next(row for row in spec if row["name"] == "EdgeFilletAxial")
    shape = predict(case, acquired["radius_m"])
    request = {"path": str(path.resolve(strict=True)), "digest": phase["output_sha256"],
               "stock_depth": case["size_mm"][2] / 1000.0,
               "expected": {"fillet_name": "ConstantEdgeFillet", "radius_m": acquired["radius_m"],
                            "edge_endpoints_m": sorted(tuple(point) for point in shape["source_edge"]),
                            "body_counts": acquired["body_counts"],
                            "volume_area_centroid_si": {"volume": volume, "area": area, "centroid": centre}}}
    run = subprocess.run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                         input=json.dumps(request), capture_output=True, text=True, timeout=90)
    require(run.returncode == 0 and not run.stderr, run.stderr)
    return {"schema": "kit.sw2026.generated-fillet-edited-read.v1", "native_result_sha256": receipt_pin,
            "native_launches": 0, "heldout_credit": 0, "result": json.loads(run.stdout)}


if __name__ == "__main__":
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--capture", type=Path)
    mode.add_argument("--edited-axial", type=Path)
    args = parser.parse_args()
    if args.worker:
        result = worker(json.load(sys.stdin))
    elif args.edited_axial:
        result = observed_axial(args.edited_axial)
    else:
        result = compare(args.capture)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
