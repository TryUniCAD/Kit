from argparse import ArgumentParser
from dataclasses import replace
from io import BytesIO
import json
from math import isclose, radians
from pathlib import Path
from subprocess import check_output, run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "PrincipalReader"), str(ROOT / "src")]
from BuildOrdinaryEndRevolves import inspect_generated, source_model
from ProveTwoDirectionRevolves import warm
from AuditPrincipalReader import make_guard
from AuditRevEndOwners import digest
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry import AdapterNotFoundError
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import PlanRevolve
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureAngleRev import AngularRevolve

FORMAT = "solidworks.sldprt"
EPOCH = 1795002026
CASES = (
    {"name": "AuditMidTop", "plane": "top", "mode": "midplane", "axis_x_m": 0.00625,
     "axis_axial_m": [-0.021, 0.030], "radius_m": [0.007, 0.023],
     "axial_m": [-0.012, 0.016], "angle_deg": 119.0, "edit_angle_deg": 157.0,
     "second_deg": 0.0, "reverse": False},
    {"name": "AuditMidRight", "plane": "right", "mode": "midplane", "axis_x_m": -0.0085,
     "axis_axial_m": [-0.028, 0.019], "radius_m": [0.009, 0.034],
     "axial_m": [-0.015, 0.004], "angle_deg": 214.0, "edit_angle_deg": 172.0,
     "second_deg": 0.0, "reverse": False},
)
RECEIPTS = {
    "RevolveEndHeldoutSourceLock01.json": "977cfab507c7c77910b752bb8c46e4968a0ddfdf7efc9a8d582d99a2c7b364b9",
    "SdkOrdinaryRevolveEndHeldout01.json": "67c41678df39397433ff94cc8183f74626df40829cad61bfbeea713addd1df88",
    "SdkTwoDirectionRevolvePublicParity01.json": "06e3c3413cc87a3060f05c815d8bafc384ffb122696377f806117584359a6eb1",
    "SdkSquareRevolveHeldoutNative01.json": "ef201f8e33168e74ae776e7e6b7efa52c9b5acb80f0d4910e565ea6ead1905be",
    "SdkSquareRevolvePublicParity01.json": "5da158ebd3f460f8e1efc9810ba94ce1326a368370a80a914e617cf42ff76d42",
}


def need(value, message):
    if not value:
        raise ValueError(message)


def refuse(action, errors, message=None):
    try:
        action()
    except errors as error:
        need(message is None or message in str(error), "unexpected refusal: " + str(error))
        return type(error).__name__
    raise ValueError("unqualified revolve request was accepted")


def study_publication(case, locator):
    values = {"final_destination": locator, "allow_non_native": True}
    opts = WriteOptions(values=values)
    document = source_model(case, locator, EPOCH)
    need(len(document.sketches[0].constraints) == 4, "authored Mid Plane rectangle requires four unary relations")
    error = "public native revolve end mode requires native acceptance"
    refuse(lambda: PlanRevolve(document), ValueError, error)
    refusal_results = {}
    for label, action, errors, detail in (
        ("registry", lambda output: write_document(document, output, destination_format=FORMAT, values=values),
         (AdapterNotFoundError,), None),
        ("direct", lambda output: SldprtWriter().write(document, output, opts),
         (ValueError,), error),
    ):
        sink = BytesIO(b"previous bytes")
        sink.seek(4)
        refusal_results[label] = refuse(lambda: action(sink), errors, detail)
        need(sink.getvalue() == b"previous bytes" and sink.tell() == 4, "unqualified write changed caller stream")
    return document, refusal_results


def study_read(raw, case, audit):
    results = {}
    angle = radians(case["angle_deg"])
    for view, include_brep in (("history", False), ("cold", True)):
        before = audit["grammar_reads"]
        doc = open_document(raw, source_format=FORMAT, strict=True,
                            include_brep=include_brep, include_tessellation=False)
        feature, = [row for row in doc.feature_timeline if type(row.definition) is AngularRevolve]
        body, = doc.bodies
        sketch, = [row for row in doc.sketches if row.id == feature.sketch_id]
        selection, = [row for row in doc.selections if row.id == feature.definition.AxisSelectionId]
        axis, = [row for row in sketch.entities if row.construction]
        driver, = [row for row in doc.parameters if row.id in feature.parameter_ids]
        need(feature.definition.SideMode == "symmetric_full" and feature.definition.AgainstParameterId is None
             and feature.definition.AlongParameterId == driver.id and driver.owner_id == feature.id
             and driver.name == "D1" and driver.role is ParameterRole.KDriving and driver.value.unit == "rad"
             and isclose(driver.value.value, angle, rel_tol=1e-14)
             and tuple(row.entity_id for row in selection.path) == (sketch.id, axis.id)
             and body.final_feature_id == feature.id,
             "strict reader lost the single total driver or actual axis/body owner")
        need(len(sketch.constraints) == 4 and {row.kind for row in sketch.constraints} == {"horizontal", "vertical"}
             and all(len(row.references) == 1 for row in sketch.constraints) and not doc.brep_payloads,
             "strict reader inferred a binary relation or introduced a stored body")
        grammar_reads = audit["grammar_reads"] - before
        if include_brep:
            need(grammar_reads == 0, "cold geometry used the legacy packaged layout")
            topology = body.topology
            ri, ro = case["radius_m"]
            lo, hi = case["axial_m"]
            volume = angle * (ro * ro - ri * ri) * (hi - lo) * 0.5e9
            area = (angle * ((ro + ri) * (hi - lo) + ro * ro - ri * ri)
                    + 2 * (hi - lo) * (ro - ri)) * 1.0e6
            need(doc.brep is not None and not doc.brep.validate(frozenset({body.id}))
                 and (topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count) == (1, 6, 12, 8)
                 and isclose(topology.volume, volume, rel_tol=1e-12)
                 and isclose(topology.surface_area, area, rel_tol=1e-12),
                 "cold geometry differs from independent angular sector")
            results["shape"] = [topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count]
        else:
            need(doc.brep is None, "history-only read produced geometry")
        results[view] = {"mode": feature.definition.SideMode, "relations": len(sketch.constraints),
                         "parameters": [driver.name], "producer_linked": True, "packaged_layout_reads": grammar_reads}
    return results


def study_matrix(case, locator):
    height = (case["radius_m"][1] - case["radius_m"][0])
    plain = dict(case, axial_m=[0.0, height])
    explicit = dict(plain, equal_edges=[1, 0])
    need(PlanRevolve(source_model(explicit, locator, EPOCH)).EqualRule == (1, 0),
         "ordered equal-length relation was not recognized")
    refuse(lambda: PlanRevolve(source_model(plain, locator, EPOCH)), ValueError,
           "public native revolve end mode requires native acceptance")
    two = dict(case, mode="two", angle_deg=92.0, second_deg=49.0)
    need(PlanRevolve(source_model(two, locator, EPOCH)).EqualRule is None,
         "qualified ordinary Two Directions gate changed")
    square_two = dict(explicit, mode="two", angle_deg=89.0, second_deg=44.0)
    need(PlanRevolve(source_model(square_two, locator, EPOCH)).EqualRule == (1, 0),
         "qualified square Two Directions gate changed")
    one = dict(explicit, mode="single", second_deg=0.0)
    refuse(lambda: PlanRevolve(source_model(one, locator, EPOCH)), ValueError,
           "public native revolve equal length requires native acceptance")
    malformed = dict(explicit, equal_edges=[0, 2])
    refuse(lambda: PlanRevolve(source_model(malformed, locator, EPOCH)), ValueError,
           "adjacent square pair")
    return ["explicit_square_mid_admitted", "square_without_equal_mid_refused",
            "ordinary_two_admitted", "explicit_square_two_admitted",
            "equal_single_refused", "opposite_pair_refused"]


def worker(case):
    warm()
    locator = "C:\\KitRevolveEndAudit\\" + case["name"] + ".SLDPRT"
    guard, audit = make_guard(ROOT / "src")
    guard["enabled"] = True
    document, refusals = study_publication(case, locator)
    memory = BytesIO()
    prepared = PrepareRevolve(document, locator, EPOCH)
    named = PrepareRevolve(document, memory, EPOCH, WriteOptions(values={"final_destination": locator}))
    need(prepared.BytesValue == named.BytesValue and not memory.getvalue(),
         "path/stream preparation changed bytes or wrote to the sink")
    initial = inspect_generated(prepared.BytesValue, case)
    need(audit["grammar_reads"] == 0, "preparation used the packaged reader layout")
    reads = study_read(prepared.BytesValue, case, audit)
    before = audit["grammar_reads"]
    state = replace(document.parameters[0], value=replace(document.parameters[0].value,
                    value=radians(case["edit_angle_deg"])))
    edited = PrepareRevolve(replace(document, parameters=(state,)), locator, EPOCH)
    edited_case = dict(case, angle_deg=case["edit_angle_deg"])
    changed = inspect_generated(edited.BytesValue, edited_case)
    need(audit["grammar_reads"] == before, "edit preparation used the packaged reader layout")
    edited_reads = study_read(edited.BytesValue, edited_case, audit)
    need(prepared.BytesValue != edited.BytesValue and initial["keyword_dimension_order"]
         == changed["keyword_dimension_order"] == ["D1"], "total angle edit did not preserve the sole driver")
    matrix = study_matrix(case, locator)
    need(not audit["unexpected_attempts"] and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
         "writer or reader attempted external access")
    return {"support": case["plane"], "original_sha256": digest(prepared.BytesValue),
            "edited_sha256": digest(edited.BytesValue), "original_streams": len(initial["streams"]),
            "edited_streams": len(changed["streams"]), "reported_views": reads, "edited_views": edited_reads,
            "public_refusals": refusals, "eligibility_matrix": matrix, "unexpected_external_accesses": len(audit["unexpected_attempts"])}


def summarize_receipts():
    records = {}
    for basename, pin in RECEIPTS.items():
        raw = (ROOT / "re/solidworks/measurements/2026" / basename).read_bytes()
        need(digest(raw) == pin, "tracked receipt identity mismatch")
        records[basename] = json.loads(raw)
    lock = records["RevolveEndHeldoutSourceLock01.json"]
    mixed = records["SdkOrdinaryRevolveEndHeldout01.json"]
    two = records["SdkTwoDirectionRevolvePublicParity01.json"]
    square = records["SdkSquareRevolveHeldoutNative01.json"]
    square_public = records["SdkSquareRevolvePublicParity01.json"]
    need(lock["passed"] and lock["distinct_processes"] == 14 and lock["writer_output_count"] == 0
         and mixed["passed"] is False and mixed["heldout_writer_cases_qualified"] == 0
         and mixed["control-before"]["passed"] and mixed["control-after"]["passed"]
         and mixed["cases"]["H-Mid-02"]["passed"] and not mixed["cases"]["H-Mid-01"]["passed"]
         and not mixed["cases"]["H-Mid-01"].get("candidate_receipt_sha256")
         and two["passed"] and two["verified_two_direction_pairs"] == 2
         and square["passed"] and square["heldout_writer_cases_qualified"] == 2 and square_public["passed"],
         "the existing native dispositions differ")
    return {"ordinary_source_lock_processes": 14, "mixed_original_qualified": 0,
            "ordinary_mid_plane_member_lifecycle_passes": 1, "ordinary_two_direction_parity": 2,
            "explicit_equal_native_lifecycle_passes": 2}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
        return
    need(run(("git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", "src"),
             check=False).returncode == 0, "the SDK source has uncommitted changes")
    sdk_tree = check_output(("git", "-C", str(ROOT), "rev-parse", "HEAD:src"), text=True).strip()
    results = []
    for case in CASES:
        completed = run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                        input=json.dumps(case), capture_output=True, text=True, check=False, timeout=90)
        need(completed.returncode == 0 and not completed.stderr, completed.stderr)
        results.append(json.loads(completed.stdout))
    print(json.dumps({"schema": "kit.sw2026.current-ordinary-revolve-end-boundary.v1",
                      "sdk_source_tree": sdk_tree, "method_sha256": digest(HERE.read_bytes()),
                      "evidence_sha256": RECEIPTS, "existing_native_dispositions": summarize_receipts(),
                      "model_only_cases": results, "private_geometry_accesses": 0,
                      "new_native_processes": 0, "new_native_acceptance": 0}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
