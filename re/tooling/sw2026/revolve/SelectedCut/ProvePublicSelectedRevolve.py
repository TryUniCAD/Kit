from argparse import ArgumentParser
from dataclasses import replace
from importlib import import_module
from io import BytesIO
from math import radians, tau
from pathlib import Path, PureWindowsPath
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "PrincipalReader")]

from AuditSelectedRevolveComposer import PACKETS, checked, digest
from BuildStockCutSelector import case_document, require, warm
from AuditPrincipalReader import make_guard
from RevolveFamilyModel import STOCK_NAMES, validate_specs, world
from VerifySdkCircleEndRegistration import OutputGuard
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry import AdapterNotFoundError
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import ReadStockAtom
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.api.ApiContext import GetRegistry
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.geometry.Models.Selection import SelectPathElem


FORMAT = "solidworks.sldprt"
POLICY = {"require_native_transfers": True}
NATIVE = {"ScopedRevolveFrontier02": "66300aa22b70a44f0b70e3e45420b426827ed8ea149a8316199bb7ee9f200258",
          "ScopedRevolveReverse03": "b310fcd0e0b25305aa2e97b2c9451673b174eac5c0376eb7cd55f4916a0ac292"}


def receipt(result, raw, path):
    require((result.path, result.adapter, result.bytes_written) == (path, FORMAT, len(raw))
            and result.vendor_loadable and result.application_usable and not result.dropped
            and not result.carrier_capabilities and not result.requirements, "native writer receipt has a loss or wrong destination")


def write_streams(writer, document, locator):
    direct, normal = BytesIO(), BytesIO()
    options = {**POLICY, "final_destination": locator}
    first = writer.write(document, direct, WriteOptions(values=options))
    second = write_document(document, normal, destination_format=FORMAT, allow_carrier=False, values=options)
    raw = normal.getvalue()
    require(raw and direct.getvalue() == raw, "direct and registry named stream bytes differ")
    receipt(first, raw, None)
    receipt(second, raw, None)
    return raw


def write_refusal(writer, document, locator, selected):
    cut = document.feature_timeline[-1]
    other = document.feature_timeline[1 - selected]
    wrong = tuple(replace(value, path=(SelectPathElem("feature", other.id, "body"),))
                  if value.id == cut.selection_ids[-1] else value for value in document.selections)
    changed = replace(document, selections=wrong)
    require(not writer.supports(changed, BytesIO()), "the writer selected a crossed stock dependency")
    for direct in (False, True):
        target = BytesIO(b"previous sink data")
        try:
            options = {**POLICY, "final_destination": locator}
            if direct:
                writer.write(changed, target, WriteOptions(values=options))
            else:
                write_document(changed, target, destination_format=FORMAT, allow_carrier=False, values=options)
        except (AdapterNotFoundError, TypeError, ValueError):
            require(target.tell() == 0 and target.getvalue() == b"previous sink data", "refusal touched the sink")
        else:
            raise ValueError("crossed stock dependency reached a native output sink")


def close(actual, expected):
    return format(actual, ".6g") == format(expected, ".6g") or abs(actual - expected) <= 1e-8


def vector(value):
    return value.x, value.y, value.z


def cold_result(raw, case, observation):
    doc = open_document(raw, source_format=FORMAT, strict=True, include_tessellation=False)
    doc.assert_valid()
    info = doc.metadata["solidworks.typed_revolve_cut"]
    require(info["status"] == "projected_cold_selection" and "result_atom_id" not in info
            and len(doc.feature_timeline) == 23 and len(doc.bodies) == len(doc.brep.bodies) == 2
            and not doc.brep_payloads and not doc.brep.validate(frozenset(value.id for value in doc.bodies)),
            "cold registry read lost its complete editable or physical owners")
    operations = [value for value in doc.feature_timeline if isinstance(value.definition, AngularRevolve)]
    expected = (tau, tau, radians(case["angle_deg"]))
    require([step.operation.value for step in operations] == ["create", "create", "cut"], "cold feature operation order differs")
    params = {value.id: value for value in doc.parameters}
    picks = {value.id: value for value in doc.selections}
    for index, (step, angle) in enumerate(zip(operations, expected, strict=True)):
        definition = step.definition
        driver = params[definition.AlongParameterId]
        direction = definition.AxisDirection
        reverse = index == 2 and case["reverse"]
        require(driver.owner_id == step.id and driver.name == "D1" and driver.role.value == "driving"
                and driver.value.unit == "rad" and close(driver.value.value, angle)
                and definition.SideMode == "one_sided" and definition.AgainstParameterId is None
                and (direction.x, direction.y, direction.z) == world(case, (0, -1 if reverse else 1, 0)),
                "cold editable sweep or signed direction differs")
    selected = operations[("inner", "outer").index(case["scope"])]
    cut = operations[-1]
    require(selected.name == observation["definition"]["scope"]["stock_owners"][0]
            and cut.input_feature_ids[-1] == selected.id
            and picks[cut.selection_ids[-1]].path == (SelectPathElem("feature", selected.id, "body"),),
            "cold portable cut lost the selected historical producer")
    expected_bodies = {row["name"]: row for row in observation["measured"].values()}
    bodies = {}
    numeric_checks = 0
    for body in doc.bodies:
        native = expected_bodies[body.name]
        topo = body.topology
        bounds = topo.bounding_box
        centre = body.attributes["solidworks.body_centroid_mm"]
        actual = (topo.volume, topo.surface_area, *centre, *vector(bounds.minimum), *vector(bounds.maximum))
        measured = (native["volume_m3"] * 1e9, native["area_m2"] * 1e6,
                    *(value * 1000 for value in (*native["com_m"], *native["bounds_m"])))
        require(all(close(left, right) for left, right in zip(actual, measured, strict=True))
                and topo.valid and topo.face_count == native["faces"] and topo.edge_count == native["edges"]
                and topo.vertex_count == native["vertices"] + 4,
                "cold analytic mass, bounds or non-seam topology differ from the native body")
        numeric_checks += len(actual)
        bodies[body.name] = {"faces": topo.face_count, "edges": topo.edge_count, "portable_vertices": topo.vertex_count,
                             "native_vertices": native["vertices"], "native_final_producer": body.final_feature_id,
                             "volume_mm3": topo.volume, "area_mm2": topo.surface_area, "centre_mm": centre}
    return {"features": len(doc.feature_timeline), "owned_D1s": len(operations), "native_mass_and_bounds_checks": numeric_checks,
            "bodies": bodies, "selected_producer_id": info["selected_producer_id"], "exact_native_axis_sense": True}


def invalid_cold(raw, mode):
    archive = SldprtArchive.from_bytes(raw)
    streams = dict(archive.streams)
    if mode == "cached_partition":
        streams["Contents/Config-0-Partition"] = b""
    else:
        link = ReadNativeLink(archive, 0)
        cut, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevCut_c")
        wrapper = cut.FieldsValue["f548"]["items"][0]["o"].FieldsValue
        (other,) = tuple(ReadStockAtom(node, False).FieldsValue["f140"]
                         for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevolution_c"
                         and ReadStockAtom(node, False).FieldsValue["f140"] != wrapper["f18"])
        wrapper["f18"] = other
        streams[link.StreamName], _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000,
                                                     link.ConfigValue.MapValue, link.ResolvedValue.ContextValue)
    try:
        open_document(BuildSldprt(streams, FormatVersion=4), source_format=FORMAT, strict=True, include_tessellation=False)
    except ValueError as error:
        require("contains no readable Parasolid payload" in str(error), str(error))
    else:
        raise ValueError("invalid or cache-present part received invented cold geometry")


def worker(request):
    warm()
    case, locator, epoch = request["case"], request["locator"], request["epoch"]
    root = Path(request["scratch"]).resolve()
    filename = case["name"] + ".SLDPRT"
    emitter = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
    emitter.ReadTime = lambda: epoch
    writer = GetRegistry().GetWriter(FORMAT)
    guard = OutputGuard(root, filename)
    sys.addaudithook(guard.audit)
    normal = root / "Published" / filename
    direct = root / "Direct" / filename
    with guard.active("memory"):
        document = case_document(case, locator, epoch)
        native = write_streams(writer, document, locator)
        require(digest(native) == request["candidate_sha256"], "exact candidate bytes differ at the measured native locator")
        write_refusal(writer, document, locator, ("inner", "outer").index(case["scope"]))
        if request["path_routes"]:
            fresh = write_streams(writer, document, str(normal))
    if request["path_routes"]:
        direct.parent.mkdir()
        with guard.active("path"):
            first = writer.write(document, direct, WriteOptions(values={**POLICY, "final_destination": str(normal)}))
            second = write_document(document, normal, allow_carrier=False, values=POLICY)
        receipt(first, fresh, direct)
        receipt(second, fresh, normal)
        require(normal.read_bytes() == direct.read_bytes() == fresh and tuple(normal.parent.iterdir()) == (normal,),
                "path and stream writes differ or left an intermediate file")
    state, audit = make_guard(ROOT / "src")
    state["enabled"] = True
    try:
        strict = cold_result(native, case, request["observed"])
        if request["path_routes"]:
            require(cold_result(fresh, case, request["observed"]) == strict, "cold read changed at the ordinary host locator")
        for mode in ("wrong_atom", "cached_partition"):
            invalid_cold(native, mode)
    finally:
        state["enabled"] = False
    require(not audit["unexpected_attempts"] and not guard.denied and not any(
        name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
        "public construction loaded an unknown file or native runtime")
    return {"sha256": digest(native), "streams": len(SldprtArchive.from_bytes(native).records),
            "named_stream_routes": 2, "fresh_path_and_stream_routes": 4 if request["path_routes"] else 0,
            "cold": strict, "runtime_writer_input_reads": 0, "unexpected_reader_input_reads": 0,
            "writer_refusals": 2, "strict_reader_refusals": 2, "passed": True}


def dispatch(script, request):
    result = run((sys.executable, "-I", "-B", str(script), "--worker"), input=json.dumps(request),
                 text=True, capture_output=True, timeout=120)
    require(result.returncode == 0 and not result.stderr, result.stderr)
    return json.loads(result.stdout)


def audit(root, scratch):
    records = {}
    for name, pin in PACKETS.items():
        packet = root / name
        manifest = json.loads(checked(packet / "Packet.json", pin))
        result = json.loads(checked(packet / "Inspection" / "Result.json", NATIVE[name]))
        require(result["passed"] and result["controls_healthy"] and result["packet_sha256"] == pin,
                "public comparison requires both native control brackets")
        for case in validate_specs(json.loads(checked(packet / "ModelSpecs.json", manifest["files"]["ModelSpecs.json"]))):
            label = case["name"]
            filename = label + ".SLDPRT"
            native = result["cases"][label]
            observed = json.loads(checked(packet / "Inspection" / label / "Initial.json", native["phases"][0]["sha256"]))
            require(native["passed"] and observed["passed"] and native["candidate_sha256"] == manifest["files"][f"Candidates/{filename}"],
                    "public comparison requires the actual native-tested candidate")
            lane = scratch / label
            lane.mkdir()
            records[label] = dispatch(HERE, {"case": case, "epoch": manifest["epoch"], "path_routes": True, "scratch": str(lane),
                                            "locator": str(PureWindowsPath(manifest["guest_workspace"]) / filename),
                                            "candidate_sha256": native["candidate_sha256"], "observed": observed["reopened"]})
    return {"schema": "kit.sw2026.public-selected-revolve-disclosure.v1", "cases": records, "fresh_processes": 4,
            "native_result_sha256": NATIVE, "new_heldout_credit": 0, "passed": True}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        args.scratch.mkdir()
        report = (json.dumps(audit(args.workspace, args.scratch), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as value:
            value.write(report)
        print(digest(report))
