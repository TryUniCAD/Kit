from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict, replace
from itertools import product
from math import nextafter
from pathlib import Path, PureWindowsPath
import json
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from VerifyAttachedAxisRead import CANDIDATE_MANIFEST, NATIVE_TRIAL, native_axes
from VerifyAttachedBoxAxes import intake
from VerifyOriginalFcstdAttachedBox import CASE, FORMAT, LOCATOR, NATIVE_SHA, ROOT, SOURCE_SHA, digest, guarded, locked, prewarm, refusal, require, source_proof, xyz
from BoxIncidence import box_incidence
from convert import open_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxes import PrincipalAxes
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxis import PrincipalAxis
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import LowerBoxModel
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import PlanAttachedBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepareBoxAxes import PrepareBoxAxes
from convert.adapters.solidworks.Core.Preparation.FreecadBox.ProjectBoxAxes import ProjectBoxAxes
from interchange import CadDocument, CadSource, Configuration, DesignBody, FeatureStep, SupportPlane, Transform, SpaceVector
from interchange.Features.FeaturePlaneAxis import PlaneAxis


BASE = "a3eba445541f84983b5dd2b7f0a9d8f24c3d8a9a"
AXES = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
DATUM_PARENTS = (("Top Plane", "Front Plane"), ("Front Plane", "Right Plane"), ("Right Plane", "Top Plane"))
VARIANTS = (
    ("OffsetNamesBox", (31.25, 14.5, 7.75), ("Plan width", "Plan length", "Depth"), ("Line A", "Line B", "Line C")),
    ("TallNeutralBox", (11.0, 23.125, 41.25), ("Horizon", "Tall reach", "Cut depth"), ("Datum X", "Datum Y", "Datum Z")),
)


def wire(document, axes, properties, locator, epoch):
    require(not document.brep_payloads and document.brep is None, "the builder would receive source payloads")
    return {
        "document": json.loads(document.to_json()),
        "axes": asdict(axes),
        "text": dict(properties.DocumentFields),
        "summary": dict(properties.SummaryFields),
        "locator": str(locator),
        "epoch": epoch,
    }


def variant(name, sizes, drivers, labels):
    locator = PureWindowsPath("C:/RecomputedAxes") / (name + ".SLDPRT")
    stock = CadDocument(
        source=CadSource("kit.neutral.box", "<independent-neutral>", digest(name.encode())),
        configurations=(Configuration("cfg", "Default", active=True),),
        parameters=(),
        support_planes=(SupportPlane("plane", "XZ-plane",
                                     Transform(y_axis=SpaceVector(0.0, 0.0, -1.0), z_axis=SpaceVector(0.0, 1.0, 0.0))),),
        sketches=(), selections=(),
        feature_timeline=(FeatureStep("boss", name + " Boss", "primitive", 0),),
        bodies=(DesignBody("body", "Named " + name, "boss"),),
    )
    model = LowerBoxModel(stock, name, ("length", "width", "height"), sizes, drivers, stock.bodies[0].name, TopAttached=True)
    axes = PrincipalAxes("Origin", True, tuple(PrincipalAxis(label, (0.0, 0.0, 0.0), direction, True)
                                                for label, direction in zip(labels, AXES, strict=True)))
    text = PartTextInput({"title": name}, {"Model label": name}, {})
    return wire(model, axes, text, locator, 1794000000), {
        "sizes": sizes, "drivers": drivers, "labels": labels, "body": stock.bodies[0].name,
    }


def prepared(request):
    fields = request["axes"]
    axes = PrincipalAxes(fields["OriginName"], fields["OriginShown"], tuple(
        PrincipalAxis(row["NameValue"], tuple(row["OriginValue"]), tuple(row["DirectionValue"]), row["IsVisible"])
        for row in fields["AxisValues"]
    ))
    model = CadDocument.from_json(json.dumps(request["document"], allow_nan=False))
    text = PartTextInput(request["summary"], request["text"], {})
    return model, axes, text, request["locator"], request["epoch"]


def byte_report(candidate):
    return {"bytes": len(candidate.BytesValue), "sha256": digest(candidate.BytesValue),
            "streams": {name: {"bytes": len(stream), "sha256": digest(stream)}
                        for name, stream in candidate.StreamsValue.items()}}


def clean_read(candidate, sizes, labels, driver_names, body_name):
    document = open_document(candidate.BytesValue, source_format=FORMAT, strict=True)
    (body,) = document.bodies
    require(document.validate() == () and body.name == body_name, "strict prepared body has invalid ownership")
    length, width, height = sizes
    topology = body.topology
    require(topology.solid_count == 1 and topology.bounding_box is not None
            and (topology.vertex_count, topology.edge_count, topology.face_count) == (8, 12, 6)
            and format(topology.volume, ".6g") == format(length*width*height, ".6g")
            and format(topology.surface_area, ".6g") == format(2*(length*width+length*height+width*height), ".6g"),
            "strict emitted topology or mass differs from independent box mathematics")
    corners = tuple(product((0.0, length), (-height, 0.0), (0.0, width)))
    shape, _ = box_incidence(document.brep, corners, body.id)
    wanted = dict(zip(driver_names, sizes, strict=True))
    require({row.name: row.value.value for row in document.parameters} == wanted, "source driver words changed")
    planes = {row.id: row.name for row in document.feature_timeline}
    actual = tuple(row for row in document.feature_timeline if isinstance(row.definition, PlaneAxis))
    intervals = tuple((low - 0.05*(high-low), high + 0.05*(high-low))
                      for low, high in ((0.0, length), (-height, 0.0), (0.0, width)))
    for index, (axis, label, supports) in enumerate(zip(actual, labels, DATUM_PARENTS, strict=True)):
        pair = (xyz(axis.definition.StartMm), xyz(axis.definition.EndMm))
        require(axis.name == label and tuple(planes[key] for key in axis.input_feature_ids) == supports
                and all(point[component] == 0.0 for point in pair for component in range(3) if component != index)
                and tuple(format(point[index], ".6g") for point in pair) ==
                    tuple(format(station, ".6g") for station in intervals[index]),
                "independent signed plane intersection disagrees with emitted selection")
    return {"body": body.name, "shape_id": shape, "parameters_mm": wanted,
            "volume_mm3": topology.volume, "area_mm2": topology.surface_area,
            "independently_predicted_axis_ranges_mm": intervals, "strict_axes": len(actual)}


def bad_inputs(model, axes, text, locator, epoch):
    first = axes.AxisValues[0]
    try_axis = lambda value: PrepareBoxAxes(model, locator, epoch, text, value)
    length = next(row for row in model.parameters if row.name == "Length")
    edited = replace(length, value=replace(length.value, value=nextafter(length.value.value, float("inf"))))
    stale = replace(model, parameters=tuple(edited if row.id == length.id else row for row in model.parameters))
    path = str(PureWindowsPath(locator).with_name("Wrong.SLDPRT"))
    return {
        "foreign_origin_label": refusal(lambda: try_axis(replace(axes, OriginName="Other Origin")),
                                        "principal axes require the actual enabled model origin"),
        "hidden_origin": refusal(lambda: try_axis(replace(axes, OriginShown=False)),
                                 "principal axes require the actual enabled model origin"),
        "hidden_axis": refusal(lambda: try_axis(replace(axes, AxisValues=(replace(first, IsVisible=False), *axes.AxisValues[1:]))),
                               "unsupported principal axis name, carrier, order or visibility"),
        "reversed_axis": refusal(lambda: try_axis(replace(axes, AxisValues=(replace(first, DirectionValue=(-1.0, 0.0, 0.0)), *axes.AxisValues[1:]))),
                                 "unsupported principal axis name, carrier, order or visibility"),
        "shifted_axis": refusal(lambda: try_axis(replace(axes, AxisValues=(replace(first, OriginValue=(0.001, 0.0, 0.0)), *axes.AxisValues[1:]))),
                                "unsupported principal axis name, carrier, order or visibility"),
        "duplicate_owner_label": refusal(lambda: try_axis(replace(axes, AxisValues=(replace(first, NameValue="Top Plane"), *axes.AxisValues[1:]))),
                                         "native part features require distinct authored names"),
        "crossed_axis_order": refusal(lambda: try_axis(replace(axes, AxisValues=axes.AxisValues[::-1])),
                                      "unsupported principal axis name, carrier, order or visibility"),
        "exact_sketch_word_disagrees": refusal(lambda: PrepareBoxAxes(stale, locator, epoch, text, axes),
                                               "attached axis stock requires exact live driver distances"),
        "unowned_document_property": refusal(lambda: PrepareBoxAxes(replace(model, metadata={**model.metadata, "display_override": True}), locator, epoch, text, axes),
                                              "plain boss candidate does not admit unprojected document metadata"),
        "wrong_basename": refusal(lambda: PrepareBoxAxes(model, path, epoch, text, axes),
                                   "native self filename must match the actual modeled part name"),
    }


def worker(request):
    require(set(request) == {"f14c"}, "writer supervisor must supply only clean neutral authoring inputs")
    lookup("utf-8-sig")
    prewarm()
    with guarded():
        model, axes, text, locator, epoch = prepared(request["f14c"])
        exact = PrepareBoxAxes(model, locator, epoch, text, axes)
        base = MakeOriginBox(model, LOCATOR, epoch, text, TopAttached=True)
        renamed = PrepareBoxAxes(model, str(PureWindowsPath("C:/OtherBoxLocator") / PureWindowsPath(locator).name),
                                epoch, text, axes)
        restamped = PrepareBoxAxes(model, locator, epoch+1, text, axes)
        require(renamed.BytesValue != exact.BytesValue and restamped.BytesValue != exact.BytesValue,
                "an alternate self locator or epoch reproduced previously measured bytes")
        known = clean_read(exact, (20.0, 30.0, 10.0), tuple(row.NameValue for row in axes.AxisValues),
                           ("Length", "Width", "Height"), model.bodies[0].name)
        alternatives = {}
        for name, sizes, drivers, labels in VARIANTS:
            payload, expected = variant(name, sizes, drivers, labels)
            document, extra_axes, extra_text, extra_locator, extra_epoch = prepared(payload)
            case = PrepareBoxAxes(document, extra_locator, extra_epoch, extra_text, extra_axes)
            alternatives[name] = {"archive": byte_report(case), "model": clean_read(
                case, expected["sizes"], expected["labels"], expected["drivers"], expected["body"]
            )}
        refusals = bad_inputs(model, axes, text, locator, epoch)
        return {
            "prepared": byte_report(exact), "ordinary_axis_free": byte_report(base),
            "strict_known": known, "independent_neutral_variants": alternatives,
            "other_locator_sha256": digest(renamed.BytesValue), "other_epoch_sha256": digest(restamped.BytesValue),
            "targeted_refusals": refusals, "runtime_input_file_reads": 0,
        }


def run_worker(request):
    child = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                           input=json.dumps(request, allow_nan=False), text=True, capture_output=True, timeout=120)
    require(child.returncode == 0 and not child.stderr, child.stderr or "guarded preparation failed")
    return json.loads(child.stdout)


def preparation_files():
    root = ROOT / "src/convert/adapters/solidworks"
    archive = root / "Archive/Construction"
    core = root / "Core/Preparation/FreecadBox"
    return (
        HERE, *sorted((archive / "Datums/PrincipalAxes").glob("*.py")), archive / "Datums/MakeHingePick.py",
        archive / "RectangleAnchors/MakeAnchorPart.py",
        *(core / (name + ".py") for name in ("CheckAxisStock", "BoxAnchorInput", "ProjectBoxAxes", "PrepareBoxAxes", "MakeOriginBoxPart")),
    )


def main():
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(json.load(sys.stdin)), allow_nan=False, sort_keys=True))
        return
    parser = ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("axis_candidate", type=Path)
    parser.add_argument("native_trial", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    measures = ROOT / "re/solidworks/measurements/2026"
    frozen = json.loads(locked(measures / "AttachedBoxAxesCandidate01.json", CANDIDATE_MANIFEST))
    old = json.loads(locked(measures / "AttachedTopBoxGeneratedNative01.json", NATIVE_SHA))["cases"][CASE]
    native = json.loads(locked(args.native_trial, NATIVE_TRIAL))
    source, raw = intake(args.source, SOURCE_SHA)
    pairs = native_axes(native, frozen, source, raw)
    source_evidence = source_proof(source, raw)
    source_plan = PlanAttachedBox(source)
    actual = source_plan.PartSource
    checked = locked(args.axis_candidate, frozen["candidate"]["sha256"])
    request = {"f14c": wire(actual.ModelValue, ProjectBoxAxes(source_plan.OriginAxes), actual.PropertiesValue,
                            frozen["exact_guest_locator"], actual.CreationEpoch)}
    report = run_worker(request)
    require(report == run_worker(request), "fresh neutral-only workers emitted different bytes or admissions")
    require(report["prepared"] == frozen["candidate"] and report["prepared"]["streams"] ==
            {name: {"bytes": len(value), "sha256": digest(value)} for name, value in SldprtArchive.from_bytes(checked).streams.items()},
            "shared builder differs from the complete Trial02 archive")
    require(report["ordinary_axis_free"]["sha256"] == old["output_sha256"] and
            report["ordinary_axis_free"]["streams"] == old["streams"],
            "common anchored preparation changed its old measured output")
    require(len({value["archive"]["sha256"] for value in report["independent_neutral_variants"].values()}) ==
            len(VARIANTS), "authored neutral contrasts emitted the same archive")
    _ = locked(args.source, SOURCE_SHA)
    _ = locked(args.axis_candidate, frozen["candidate"]["sha256"])
    result = {"schema": "kit.sw2026.attached-box-axes-sdk-preparation.v1", "passed": True,
              "base": BASE, "source_sha256": SOURCE_SHA, "intact_document_capabilities": sorted(map(str, GetDocumentCaps(source))),
              "native_trial_sha256": NATIVE_TRIAL, "candidate_manifest_sha256": CANDIDATE_MANIFEST,
              "native_locator": frozen["exact_guest_locator"], "creation_epoch": actual.CreationEpoch,
              "source_axis_associations": pairs, "source_evidence": {
                  key: source_evidence[key] for key in ("document_xml_sha256", "native_binding_sha256", "shape_owners",
                                                       "source_provenance_owners", "object_owners")},
              "guarded_child_processes": 2, "new_native_processes": 0,
              "prior_control_receipt_sha256": NATIVE_SHA, "corpus_conversion_credits": 0, "new_heldout_credits": 0,
              "changed_preparation_files_sha256": {str(file.relative_to(ROOT)): digest(file.read_bytes())
                                                   for file in preparation_files()}, **report}
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, allow_nan=False, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
