from argparse import ArgumentParser
from dataclasses import asdict, replace
from io import BytesIO
from json import dumps, loads
from math import cos, dist, sin
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from CheckMeasuredAngle import EPOCH, MEASURE, NATIVE, RESULT, ROOT, TRIAL, canonical, digest, locked, reject
from CheckWarmAngle import ARCHIVE, SOURCE, SPEC, prove as preserved_source, warm_modules
from ChamferModel import compare_six, predict, values_si
from ProvePublicChamferWrite import authored
from SavedChmfDisplay import compare_displays, display_rows, exterior_scores, read_intent
from VerifySdkCircleEndRegistration import OutputGuard
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Chamfers.EmitChmfPart import EmitChmfPart
from convert.adapters.solidworks.Archive.Construction.Chamfers.Views.ChmfViewInput import ChmfViewInput
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import NativePartModel
from convert.adapters.solidworks.Core.Partition.PartMass import ReadPartMass
from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import PlanChmfPart
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.BuildChmfGeom import BuildChmfGeom, ChmfPrism
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfCold import CheckChmfCold
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import ChmfPartRead
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import CoordsChmf, JoinChmfEdge
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import ReadChmfOwn
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRoots import ReadChmfRoots
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import ReadChmfRows
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfStock import ReadChmfStock
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.ReadWarmChmf import ReadWarmChmf
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import IsCacheAbsent
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

BASE = "4f3fe8ee989b7df7b15c9b87c29793617047e1aa"
ARC = "7a696419144538fb6e876e568d633ce9f05a8cc3d57c0bcacf06ce7204e2f2f0"
SAVED_SDK = "4912e9b409b2d4d8ccd443c83fa5a690ea3b5eb03f82330f827c77120372fc73"
VERSION = 19000


def replay(archive, link):
    config, resolved = link.ConfigValue, link.ResolvedValue
    config_data, new_config = WriteConfigMut(config.RootValue, VERSION, config.HeaderValue)
    raw, new_resolved = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, VERSION,
                                      new_config.MapValue, resolved.ContextValue, WriteChamfers=True)
    assert config_data == archive.require(link.ConfigName) and raw == archive.require(link.StreamName)
    assert config.MapValue == new_config.MapValue and resolved.MapValue == new_resolved.MapValue
    return {link.ConfigName: digest(config_data), link.StreamName: digest(raw)}


def selections(edge):
    return {
        "edge_point_mm": CoordsChmf(edge.EdgePoint), "distance_face_point_mm": CoordsChmf(edge.FacePoint),
        "edge_axis": edge.EdgeAxis, "distance_axis": edge.DistanceAxis, "corner": edge.CornerBits,
    }


def read_source(request):
    payload = bytes.fromhex(request["payload"])
    original = preserved_source(request, payload)
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    native = NativePartModel(archive, "Default", StrictRefs=True)
    source = ReadWarmChmf(archive, native, link)
    digests = replay(archive, link)
    intent = read_intent(link, source.OwnersValue)
    header = ReadHeaderGraph(archive.require("Header2"), VERSION)
    roles = ReadChmfRows(link, source.OwnersValue, header, IsSaved=True)
    assert replay(archive, link) == digests
    assert source.WarmValue is not None and original["shape"]["matches_stored_brep"]
    return {
        "source": original, "linked_stream_sha256": digests,
        "view": asdict(intent), "displays": display_rows(source.OwnersValue),
        "selection": selections(source.EdgeValue), "ordered_roles": roles,
    }


def model_intent(wire):
    assert set(wire) == {"CatalogValue", "DriverView", "DistanceText", "AngleText",
                         "WitnessLength", "DesignIntent", "LeadersValue"}
    views = tuple(AnnoViewInput(row["NameValue"], tuple(map(tuple, row["BasisValue"])))
                  for row in wire["CatalogValue"])
    return ChmfViewInput(views, wire["DriverView"], tuple(wire["DistanceText"]), tuple(wire["AngleText"]),
                         wire["WitnessLength"], wire["DesignIntent"], tuple(wire["LeadersValue"]))


def construct(request):
    assert request.keys() == {"case", "side", "view", "contrast"}
    case, side = request["case"], request["side"]
    document = authored(case, side)
    plan = PlanChmfPart(document)
    intent = model_intent(request["view"])
    settings = replace(MakePartRecipe(plan.StockValue, EPOCH),
                       OutputValue=SelfFileInput("C:\\KitChmfDisplay\\" + case["name"] + ".SLDPRT", EPOCH))
    plan = replace(plan, DisplayValue=intent)
    built = EmitChmfPart(document, plan, settings)
    archive = SldprtArchive.from_bytes(built.BytesValue)
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    owners = ReadChmfOwn(link, ColdValue=True)
    CheckChmfCold(link, owners)
    dims = [row.ValueSi for row in owners.DriversValue]
    assert tuple(dims) == values_si(case, False)
    roots, nodes = ReadChmfRoots(link, NativePartModel(archive, "Default", StrictRefs=True), owners.FeatureValue)
    stock, prism, loop = ReadChmfStock(link, owners.StockValue, nodes)
    header = ReadHeaderGraph(archive.require("Header2"), VERSION)
    roles = ReadChmfRows(link, owners, header)
    edge = JoinChmfEdge(prism, loop, roles)
    part = ChmfPartRead(link, owners, stock, ChmfPrism(link, owners, edge), edge, roots)
    geometry = BuildChmfGeom(part, plan.StockValue.BodyId)
    expected = predict(case, tuple(dims), (side, "tan"))
    topology = geometry.TopologyValue
    mass = ReadPartMass(geometry.BrepValue, topology.bounding_box)
    assert mass is not None
    source_numbers = (expected["volume"], expected["area"], *expected["com"])
    actual_numbers = (
        mass.Volume * 1e-9, topology.surface_area * 1e-6, *(value * 0.001 for value in mass.Centroid)
    )
    assert all(compare_six(actual, wanted, 1e-12)[2]
               for actual, wanted in zip(actual_numbers, source_numbers, strict=True))
    assert sorted(tuple(round(value * 0.001, 12) for value in CoordsChmf(row.point))
                  for row in geometry.BrepValue.vertices) == sorted(
        tuple(round(value, 12) for value in point) for point in expected["vertices"]
    )
    assert IsCacheAbsent(archive)
    read_view = read_intent(link, owners)
    assert read_view.CatalogValue == intent.CatalogValue and read_view.DriverView == intent.DriverView
    assert read_view.DistanceText == intent.DistanceText and read_view.LeadersValue == intent.LeadersValue
    assert read_view.DesignIntent == intent.DesignIntent and dist(read_view.AngleText, intent.AngleText) <= 1e-12
    assert abs(read_view.WitnessLength - intent.WitnessLength) <= 1e-12
    rejects = refuse_contrasts(document, plan, settings) if request["contrast"] else []
    return {
        "archive_sha256": digest(built.BytesValue), "linked_stream_sha256": replay(archive, link),
        "streams": len(archive.streams), "contains_saved_partition": False,
        "analytic_mass_and_area_checks": len(actual_numbers), "analytic_vertices": len(expected["vertices"]),
        "displays": display_rows(owners), "selection": selections(edge), "ordered_roles": roles,
        "refused": rejects,
    }


def refuse_contrasts(document, plan, settings):
    intent = plan.DisplayValue
    missing = replace(intent, DriverView="Missing view")
    index = next(i for i, row in enumerate(intent.CatalogValue) if row.NameValue == intent.DriverView)
    chosen = intent.CatalogValue[index]
    u_axis, v_axis, normal = chosen.BasisValue
    turned = replace(chosen, BasisValue=(v_axis, tuple(-value for value in u_axis), normal))
    mismatched = (*intent.CatalogValue[:index], turned, *intent.CatalogValue[index + 1:])
    sense = 1 if intent.DistanceText[1] > 0 else -1
    interior = (0.01 * sense * cos(plan.AngleValue / 2), -0.01 * sense * sin(plan.AngleValue / 2))
    cases = {
        "missing_view": (replace(plan, DisplayValue=missing), "one actual named driver view"),
        "turned_view": (replace(plan, DisplayValue=replace(intent, CatalogValue=mismatched)), "both signed incident axes"),
        "swapped_view_alias": (replace(plan, DisplayValue=replace(intent, CatalogValue=(*intent.CatalogValue, chosen))),
                               "one actual named driver view"),
        "wrong_clearance_side": (replace(plan, DisplayValue=replace(intent, DistanceText=(
            intent.DistanceText[0], -intent.DistanceText[1]))), "wrong signed witness side"),
        "interior_text": (replace(plan, DisplayValue=replace(intent, AngleText=interior)), "exterior witness placement"),
        "boundary_text": (replace(plan, DisplayValue=replace(intent, AngleText=(sense * 0.01, 0.0))),
                          "exterior witness placement"),
        "linear_mode": (replace(plan, AngleValue=None), "one live distance and one angle"),
    }
    for altered, reason in cases.values():
        reject(lambda: EmitChmfPart(document, altered, settings), reason)
    return list(cases)


def worker(role, request):
    warm_modules()
    with TemporaryDirectory(prefix="KitChmfView.") as temp:
        guard = OutputGuard(Path(temp), "unexpected")
        sys.addaudithook(guard.audit)
        with guard.active("memory"):
            result = read_source(request) if role == "source" else construct(request)
    assert not guard.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules)
    return result | {"runtime_accesses": len(guard.denied)}


def launch(role, request):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker", role),
                 input=dumps(request, allow_nan=False), capture_output=True, text=True, timeout=120, check=False)
    assert result.returncode == 0 and not result.stderr, result.stderr
    return loads(result.stdout)


def compare(source, candidate):
    assert source["ordered_roles"] == candidate["ordered_roles"], (
        source["ordered_roles"], candidate["ordered_roles"]
    )
    for key, value in source["selection"].items():
        if key.endswith("_mm"):
            assert dist(value, candidate["selection"][key]) <= 1e-9, (key, value, candidate["selection"])
        else:
            assert value == candidate["selection"][key]
    counts = compare_displays(source["displays"], candidate["displays"])
    return {
        "archive_sha256": candidate["archive_sha256"], "linked_stream_sha256": candidate["linked_stream_sha256"],
        "exact_typed_roles": candidate["ordered_roles"], "map_owned_driver_ids": [
            row["driver_id"] for row in candidate["displays"]
        ],
        "comparison": counts, "cold_cache_absent": not candidate["contains_saved_partition"],
        "analytic_mass_and_area_checks": candidate["analytic_mass_and_area_checks"],
        "analytic_vertices": candidate["analytic_vertices"],
        "refused": candidate["refused"],
    }


def supervise(source, output):
    source, output = source.resolve(), output.resolve()
    assert not output.is_relative_to(source) and not output.is_relative_to(ROOT)
    arc = locked(RESULT / "LocalLinearPatternAngularArc01.json", ARC)
    assert arc["static_owners"]["constants"]["outside_second_witness"] == ["0x4cde9a88", 1.5]
    receipt = locked(RESULT / "EdgeChamferDisclosedSource01.json", SOURCE)
    archive = locked(RESULT / "EdgeChamferTypedArchiveRead01.json", ARCHIVE)
    saved = locked(RESULT / "SdkSavedAngleChamfer01.json", SAVED_SDK)
    spec_bytes = HERE.with_name("DisclosedChamferInputs.json").read_bytes()
    assert digest(spec_bytes) == SPEC
    assert receipt["passed"] and receipt["oracle_build"] == "34.5.2.0604"
    assert receipt["distinct_processes"] == 8 and all(row["passed"] for row in receipt["controls"].values())
    assert archive["disclosed_lock_sha256"] == saved["disclosed_lock_sha256"] == SOURCE
    trial = locked(RESULT / "ChamferSignedSideTrial01.json", TRIAL)
    native = locked(RESULT / "ChamferSignedSideNative01.json", NATIVE)
    options = {"final_destination": trial["cases"][0]["locator"], MEASURE: {
        "written_at": EPOCH, "receipt": {"trial": trial, "native_result": native},
    }}
    cases = []
    for case, authority in zip(loads(spec_bytes)["cases"], receipt["sources"], strict=True):
        for edited, phase in ((False, "original"), (True, "edited")):
            row, = (value for value in archive["disclosed_parts"] if (value["case"], value["edited"]) == (case["name"], edited))
            assert authority[phase + "_sha256"] == row["source_sha256"]
            filename = case["name"] + ("Edited" if edited else "") + ".SLDPRT"
            payload = (source / filename).read_bytes()
            assert digest(payload) == row["source_sha256"]
            request = {"case": case, "branch": authority["orientation"], "archive_evidence": row,
                       "edited": edited, "payload": payload.hex(), "write_options": options}
            observed = launch("source", request)
            expected = next(value for value in saved["cases"] if value["source_sha256"] == row["source_sha256"])
            observed_source = dict(observed["source"], runtime_accesses=observed["runtime_accesses"])
            assert observed_source == expected, {
                key: (expected[key], observed_source.get(key)) for key in expected
                if expected[key] != observed_source.get(key)
            }
            model = {"case": case | (case["edit"] if edited else {}), "side": authority["orientation"][0],
                     "view": observed["view"], "contrast": True}
            built, repeated = (launch("construct", model) for _ in range(2))
            assert built == repeated
            cases.append({"source_sha256": row["source_sha256"], "case": case["name"], "phase": phase,
                          "source_view": observed["view"], "source_linked_sha256": observed["linked_stream_sha256"],
                          "source_stations": [row["station"] for row in observed["displays"]],
                          "source_exterior_scores": exterior_scores(observed["displays"][1]),
                          "source_flags_outside_projection": [row["unclassified_f8a4"] for row in observed["displays"]],
                          "source_warm_state": observed["source"]["shape"], "source_still_refuses_publication": True,
                          "generated_scope": compare(observed, built), "intent_sha256": digest(canonical(model)),
                          "runtime_accesses": built["runtime_accesses"] + observed["runtime_accesses"] + repeated["runtime_accesses"]})
    assert [row["source_stations"][1] for row in cases] == [1.5, 1.5, 1.5, -0.5]
    construction = ROOT / "src/convert/adapters/solidworks/Archive/Construction/Chamfers"
    paths = [HERE, HERE.with_name("SavedChmfDisplay.py"), *construction.glob("*.py"), *(construction / "Views").glob("*.py")]
    report = {
        "schema": "kit.sw2026.chamfer-explicit-driver-display.v1", "base": BASE, "oracle_build": receipt["oracle_build"],
        "disclosed_lock_sha256": SOURCE, "typed_archive_sha256": ARCHIVE, "saved_sdk_sha256": SAVED_SDK,
        "angular_static_evidence_sha256": ARC, "guarded_source_processes": 4, "guarded_model_processes": 8,
        "new_native_processes": 0, "new_heldout_cases": 0, "published_cad_files": 0,
        "sources": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in paths}, "cases": cases,
    }
    with output.open("xb") as stream:
        stream.write(canonical(report))
    print(digest(output.read_bytes()))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--worker"] and len(sys.argv) == 3 and sys.argv[2] in ("source", "construct"):
        print(dumps(worker(sys.argv[2], loads(sys.stdin.read())), allow_nan=False))
    else:
        parser = ArgumentParser()
        parser.add_argument("--source", type=Path, required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args()
        supervise(args.source, args.output)
