from argparse import ArgumentParser
from dataclasses import replace
from functools import partial
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from subprocess import run
import codecs
import json
import math
import os
import sys

ROOT = Path(__file__).resolve().parents[5]
LOCK = ROOT / "re/solidworks/v2026/heldout/PrincipalRevolveSourceLock01.json"
LOCK_HASH = "9396b94d1d503a0389c1db4ce7711125429265b271694bbe28a890b49059dc48"
BUILD = "34.5.2.0604"
BUILD_HASH = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BASELINE = "03e2e5ed376229565c6d381b132dd1c946d89218"
RIGHT_NAME = "PrincipalRevolveRightReverse"
RIGHT_SHA = "0c3ef35a0f8412895cf870359df037ae3450aad45abaa426767838894e18e681"
RIGHT_RECEIPT = "83f0043cf3ce9a8c68ffbbc329681bfc3a887edc0f65851f9f8da7db44b09f01"
RIGHT_REOPEN = "4b49e414e21229f93f0b704e0a0468babf6cc21f58960884363cb40f6c93eca1"
CASES = {
    "PrincipalRevolveFrontFull": ("front", 2),
    "PrincipalRevolveTopForward": ("top", 3),
    "PrincipalRevolveTopReverse": ("top", 3),
    RIGHT_NAME: ("right", 4),
}
FRAMES = {
    "front": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "top": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "right": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
}
GRAMMAR = "convert/adapters/solidworks/Config/RootLayout.json"


def digest(raw):
    return sha256(raw).hexdigest()


def to_xyz(value):
    return value.x, value.y, value.z


def point(plane, u, v):
    x, y, _ = FRAMES[plane]
    return tuple(u * a + v * b for a, b in zip(x, y, strict=True))


def check_projection(document, plane, plane_id, local, angle, reverse):
    from interchange.Features.FeatureAngleRev import AngularRevolve

    document.assert_valid()
    meta = document.metadata["solidworks.typed_revolve_semantics"]
    assert meta["status"] == "projected"
    assert meta["revolutions"][0]["scope"] == f"ordinary_modern_single_blind_rectangular_boss_{plane}_upward_axis"
    (feature,) = [value for value in document.feature_timeline if type(value.definition) is AngularRevolve]
    (sketch,) = [value for value in document.sketches if value.id == feature.sketch_id]
    (support,) = [value for value in document.support_planes if value.id == f"sldprt:plane:{plane_id}"]
    assert sketch.support_plane_id == support.id and to_xyz(support.transform.origin) == (0, 0, 0)
    assert tuple(to_xyz(value) for value in (support.transform.x_axis, support.transform.y_axis,
                                              support.transform.z_axis)) == FRAMES[plane]
    assert len(sketch.entities) == 5 and len(sketch.constraints) == 4
    (path,) = [value for value in document.selections if value.id == feature.definition.AxisSelectionId]
    (driver,) = [value for value in document.parameters if value.id == feature.definition.AlongParameterId]
    (axis,) = [value for value in sketch.entities if value.construction]
    assert tuple((value.entity_kind, value.entity_id) for value in path.path) == (
        ("sketch", sketch.id), ("sketch_entity", axis.id)
    )
    assert tuple((p.x, p.y) for p in (axis.geometry.start, axis.geometry.end)) == local
    assert feature.parameter_ids == (driver.id,) and feature.selection_ids == (path.id,)
    assert driver.name == "D1" and driver.owner_id == feature.id and driver.value.unit == "rad"
    assert driver.value.value == angle and driver.role.value == "driving"
    world = tuple(point(plane, u, v) for u, v in local)
    direction = tuple((-1 if reverse else 1) * value for value in FRAMES[plane][1])
    assert to_xyz(feature.definition.AxisOrigin) == world[0]
    assert to_xyz(feature.definition.AxisDirection) == direction
    assert path.attributes["native_ordered_endpoints_mm"] == world
    assert path.attributes["native_reverse_direction"] is reverse
    assert feature.attributes["native_reverse_direction"] is reverse
    return {"feature": feature.id, "driver": driver.id, "axis": axis.id, "plane": support.id,
            "local_mm": local, "world_mm": world, "direction": direction, "radians": angle}


def disclosed_state(folder, case):
    name = case["name"]
    data = (folder / f"{name}.SLDPRT").read_bytes()
    receipts = tuple((folder / f"{name}.{phase}.json").read_bytes() for phase in ("author", "reopen"))
    assert len(data) == case["native_bytes"] and digest(data) == case["native_sha256"]
    assert [digest(raw) for raw in receipts] == case["phase_record_sha256"]
    author, reopen = map(json.loads, receipts)
    for phase in (author, reopen):
        oracle = phase["oracle_identity"]
        assert oracle["file_version"] == BUILD and oracle["sha256"] == BUILD_HASH
        assert phase["passed"] and phase["inspection_completed"] and not phase["dialogs"]
    assert case["dimension_edit_passed"]
    return checked_reopen(data, reopen)


def disclosed_right(paths):
    raw, receipt_raw, reopen_raw = (Path(path).read_bytes() for path in paths)
    assert (digest(raw), digest(receipt_raw), digest(reopen_raw)) == (RIGHT_SHA, RIGHT_RECEIPT, RIGHT_REOPEN)
    receipt, reopen = map(json.loads, (receipt_raw, reopen_raw))
    assert receipt["case"] == reopen["job"]["case"]
    assert receipt["case"]["name"] == RIGHT_NAME and receipt["case"]["split"] == "discovery"
    assert receipt["passed"] and receipt["controls_healthy"] and receipt["distinct_processes"] == 4
    assert len({phase["native_process_birth"] for phase in receipt["phases"]}) == 4
    assert all(phase["passed"] for phase in receipt["phases"])
    assert receipt["native_sha256"] == digest(raw) and receipt["native_bytes"] == len(raw)
    assert receipt["sealed_inputs_read"] == receipt["writer_outputs"] == receipt["new_heldout_credit"] == 0
    assert receipt["oracle"]["version"] == reopen["oracle_identity"]["file_version"] == BUILD
    assert receipt["oracle"]["sha256"] == reopen["oracle_identity"]["sha256"] == BUILD_HASH
    assert reopen["passed"] and reopen["inspection_completed"] and not reopen["dialogs"]
    assert receipt["initial"]["mass"] == reopen["reopened"]["mass"]
    assert receipt["edited"]["angle_radians"] == reopen["edited"]["angle_radians"]
    return checked_reopen(raw, reopen)


def checked_reopen(data, reopen):
    assert reopen["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
    state = reopen["reopened"]
    assert state["bodies"] == 1 and reopen["display_dimensions"][0]["editable"]
    assert reopen["display_dimensions"][0]["name"].startswith("D1@")
    assert reopen["display_dimensions"][0]["value"] == state["angle_radians"]
    assert reopen["edit"]["passed"]
    return data, state, reopen["edit"]


def make_guard(sdk):
    gram = (sdk / GRAMMAR).resolve()
    receipt = {"grammar_path": GRAMMAR, "grammar_sha256": digest(gram.read_bytes()),
               "grammar_reads": 0, "unexpected_attempts": []}
    state = {"enabled": False}

    def audit(event, args):
        if not state["enabled"]:
            return
        if event == "open" and args[0] == str(gram) and (args[2] & os.O_ACCMODE) == os.O_RDONLY:
            receipt["grammar_reads"] += 1
            return
        if (event in ("open", "os.listdir", "os.scandir", "os.system", "os.fork",
                      "os.posix_spawn", "ctypes.dlopen") or event.startswith(("subprocess.", "socket."))):
            receipt["unexpected_attempts"].append(event)
            raise RuntimeError(f"unexpected reader access: {event} {args[0] if args else ''}")

    sys.addaudithook(audit)
    return state, receipt


def inspect_saved(data, native, edit, plane, plane_id, original):
    from convert import open_document
    from interchange.document.Behavior.DocumentIo import ToJson

    report = {}
    for name, options in (("default", {}), ("semantics", {"include_brep": False, "include_tessellation": False})):
        doc = open_document(data, source_format="solidworks.sldprt", strict=True, **options)
        doc.assert_valid()
        row = {"document_sha256": digest(ToJson(doc).encode()),
               "projected": doc.metadata.get("solidworks.typed_revolve_semantics", {}).get("status") == "projected"}
        if original and plane != "front":
            assert not row["projected"]
        else:
            local = tuple((a * 1000.0, b * 1000.0) for a, b, _ in native["axis"]["points"])
            row["projection"] = check_projection(doc, plane, plane_id, local, native["angle_radians"], native["reverse"])
        if name == "default":
            assert doc.brep is not None and len(doc.brep.bodies) == len(doc.bodies) == 1
            assert not any(item.code == "sldprt.brep_reconstructed" for item in doc.diagnostics)
            assert tuple(payload.kind for payload in doc.brep_payloads) == ("partition", "deltas")
            row["payloads"] = [payload.sha256 for payload in doc.brep_payloads]
            row["native_brep_counts"] = {
                "faces": len(doc.brep.faces), "vertices": len(doc.brep.vertices),
            }
            vertices = tuple(to_xyz(vertex.point) for vertex in doc.brep.vertices)
            if plane != "front":
                coordinate = 1 if plane == "top" else 0
                almost_zero = 1e-9
                signed = tuple(value[coordinate] for value in vertices)
                if native["reverse"]:
                    assert min(signed) >= -almost_zero and max(signed) > 0
                else:
                    assert min(signed) < 0 and max(signed) <= almost_zero
                row["native_vertex_bounds_signed_mm"] = (min(signed), max(signed))
            row["bound_name"] = doc.metadata.get("solidworks.native_body_names", {}).get("status") == "complete"
            row["body"] = doc.bodies[0].name
            if not original or plane == "front":
                assert row["bound_name"] and row["body"] == "OrdinaryBossRevolve"
                assert doc.brep.bodies[0].design_body_id == doc.bodies[0].id
                assert not doc.brep.validate(frozenset((doc.bodies[0].id,)))
        else:
            assert doc.brep is None and not doc.brep_payloads
        report[name] = row
    return {"modes": report, "original_native_edit_angle_radians": edit["after_radians"],
            "original_native_saved_edit_supplied": False, "oracle_mass_properties": native["mass"]}


def inspect_cold(payload, spec, axis, reverse):
    from convert import open_document

    plane = {"x": "right", "y": "top", "z": "front"}[axis]
    doc = open_document(payload, source_format="solidworks.sldprt", strict=True)
    local = tuple((spec["axis_x_mm"] * 0.001 * 1000.0, value * 0.001 * 1000.0)
                  for value in spec["axis_span_mm"])
    projection = check_projection(doc, plane, spec["support_id"], local,
                                  spec["angle_rad"], reverse)
    assert doc.brep is not None and not doc.brep_payloads
    assert any(item.code == "sldprt.brep_reconstructed" for item in doc.diagnostics)
    (body,) = doc.bodies
    assert body.final_feature_id == projection["feature"]
    assert not doc.brep.validate(frozenset((body.id,)))
    assert (body.topology.solid_count, body.topology.shell_count, body.topology.face_count) == (1, 1, 6)
    ri, ro = spec["radial_mm"]
    lo, hi = spec["axial_mm"]
    angle = spec["angle_rad"]
    height = hi - lo
    volume = angle * height * (ro**2 - ri**2) / 2
    area = angle * ((ro + ri) * height + ro**2 - ri**2) + 2 * (ro - ri) * height
    assert math.isclose(body.topology.volume, volume, rel_tol=1e-12)
    assert math.isclose(body.topology.surface_area, area, rel_tol=1e-12)
    bounds = body.topology.bounding_box
    amin, amax = to_xyz(bounds.minimum), to_xyz(bounds.maximum)
    coordinate = {"x": 0, "y": 1, "z": 2}[axis]
    reach = ro * math.sin(angle)
    assert math.isclose(amin[coordinate], 0 if reverse else -reach, abs_tol=1e-12)
    assert math.isclose(amax[coordinate], reach if reverse else 0, abs_tol=1e-12)
    return {"bytes": len(payload), "sha256": digest(payload), "projection": projection,
            "volume_mm3": volume, "area_mm2": area, "bounds_mm": (amin, amax)}


def worker(sdk):
    sys.path[:0] = [str(sdk), str(Path(__file__).resolve().parent)]
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
    request = json.load(sys.stdin)
    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for module in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.AngleRevValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Validation.PlaneRevValidate",
        "interchange.document.Validation.DistExtValidate",
    ):
        import_module(module)
    if request["mode"] == "native":
        if "right" in request:
            data, native, edit = disclosed_right(request["right"])
            case_name = RIGHT_NAME
        else:
            case = request["case"]
            case_name = case["name"]
            assert case["split"] == "discovery" and case_name in CASES and case_name != RIGHT_NAME
            data, native, edit = disclosed_state(Path(request["folder"]), case)
        plane, plane_id = CASES[case_name]
        inspect = partial(inspect_saved, data, native, edit, plane, plane_id, request["baseline"])
    else:
        from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.CheckRevSupport import CheckRevSupport
        from MakePrincipalCold import make_cold
        def inspect():
            axis = request["axis"]
            reverse = request["reverse"]
            data, spec = make_cold(axis, reverse, request["rotated"])
            again, _ = make_cold(axis, reverse, request["rotated"])
            assert data == again
            if not request["rotated"]:
                output = inspect_cold(data, spec, axis, reverse)
                if axis != "z":
                    document = open_document(data, source_format="solidworks.sldprt", strict=True)
                    link = ReadNativeLink(SldprtArchive.from_bytes(data), 0)
                    (owner,) = ReadRevOwners(link)
                    (sketch,) = document.sketches
                    other = next(plane for plane in document.support_planes if plane.id != sketch.support_plane_id)
                    spoofed = replace(sketch, support_plane_id=other.id)
                    try:
                        CheckRevSupport(document, spoofed, owner)
                    except ValueError as error:
                        assert str(error) == "ordinary revolve public support differs from its actual datum"
                        output["forged_public_support_refused"] = str(error)
                    else:
                        raise AssertionError("a foreign public support was accepted")
                return output
            try:
                ReadRevOwners(ReadNativeLink(SldprtArchive.from_bytes(data), 0))
            except ValueError as error:
                assert str(error) == "boss support must be a canonical principal frame at origin"
                try:
                    open_document(data, source_format="solidworks.sldprt", strict=True)
                except ValueError as public:
                    return {"refused": str(error), "public_refusal": str(public), "sha256": digest(data)}
                raise AssertionError("a rotated principal frame entered the default cold route")
            raise AssertionError("rotated principal frame was projected")
    state, accesses = make_guard(sdk)
    state["enabled"] = True
    try:
        output = inspect()
    finally:
        state["enabled"] = False
    assert not accesses["unexpected_attempts"]
    assert all(Path(module.__file__).resolve().is_relative_to(sdk.resolve())
               for name, module in sys.modules.items()
               if (name == "convert" or name.startswith(("convert.", "interchange."))) and getattr(module, "__file__", None))
    if request["mode"] == "cold":
        assert accesses["grammar_reads"] == 0
    print(json.dumps(output | {"guard": accesses}, sort_keys=True, allow_nan=False))


def launch(sdk, request):
    result = run((sys.executable, "-I", "-B", __file__, "--worker", str(sdk)), input=json.dumps(request),
                 capture_output=True, text=True, check=False, timeout=90)
    if result.returncode or result.stderr:
        raise ValueError(f"{request}: {result.stderr}")
    return json.loads(result.stdout)


def main(args):
    raw = LOCK.read_bytes()
    assert digest(raw) == LOCK_HASH
    lock = json.loads(raw)
    assert lock["heldout_results_sealed"] and lock["passed"] and lock["oracle_sha256"] == BUILD_HASH
    assert lock["control_before_healthy"] and lock["control_after_healthy"]
    cases = tuple(row for row in lock["cases"] if row["split"] == "discovery")
    assert {row["name"] for row in cases} == set(CASES) - {RIGHT_NAME}
    native = {}
    requests = {case["name"]: {"mode": "native", "case": case, "folder": str(args.sources.resolve())} for case in cases}
    requests[RIGHT_NAME] = {"mode": "native", "right": [str(path.resolve()) for path in args.right]}
    for case_name, request in requests.items():
        before = launch(args.baseline_sdk.resolve(), request | {"baseline": True})
        after = launch(ROOT / "src", request | {"baseline": False})
        for mode in ("default", "semantics"):
            assert before["modes"][mode]["projected"] is (CASES[case_name][0] == "front")
            assert after["modes"][mode]["projected"]
        assert before["modes"]["default"]["payloads"] == after["modes"]["default"]["payloads"]
        if CASES[case_name][0] == "front":
            assert before == after
        pinned = request["case"] if case_name != RIGHT_NAME else {
            "native_sha256": RIGHT_SHA, "native_receipt_sha256": RIGHT_RECEIPT, "reopen_sha256": RIGHT_REOPEN,
        }
        native[case_name] = {"pinned": pinned, "baseline": before, "candidate": after}
    cold = {}
    for axis, reverse, rotated in (("z", False, False), ("y", False, False),
                                   ("y", True, False), ("x", True, False),
                                   ("y", False, True), ("x", False, True)):
        tag = f"{axis}-{int(reverse)}-{int(rotated)}"
        cold[tag] = launch(ROOT / "src", {"mode": "cold", "axis": axis, "reverse": reverse,
                                         "rotated": rotated})
    report = {"schema": "kit.sw2026.principal-revolve-reader.v1", "baseline_revision": BASELINE,
              "source_lock_sha256": LOCK_HASH, "oracle_sha256": BUILD_HASH, "oracle_build": BUILD,
              "native_launches": 0, "heldout_inputs_read": 0,
              "guarded_processes": len(native) * 2 + len(cold),
              "methods": {name: digest((Path(__file__).resolve().parent / name).read_bytes())
                          for name in ("AuditPrincipalReader.py", "MakePrincipalCold.py")},
              "reader_sources": {name: digest((ROOT / "src/convert/adapters/solidworks/Core/TypedResolved/Revolves" / name).read_bytes())
                                 for name in ("ReadRevFrame.py", "Projection/ApplyRevDoc.py", "Projection/CheckRevSupport.py",
                                              "Projection/ReportRevolve.py")},
              "native": native, "authored_cold": cold}
    encoded = (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as file:
        file.write(encoded)
    print(json.dumps({"guarded_processes": report["guarded_processes"], "sha256": digest(encoded)}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--baseline-sdk", type=Path)
    parser.add_argument("--right", type=Path, nargs=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
    else:
        main(args)
