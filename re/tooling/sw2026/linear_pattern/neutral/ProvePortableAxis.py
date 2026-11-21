from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from math import sqrt
from pathlib import Path
from subprocess import check_output, run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent),
                str(HERE.parents[2]), str(HERE.parents[2] / "serial")]

from interchange import CadDocument, PlaneAxis, history
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.serialization.EncodeData import ToData
from interchange.serialization.TypeRegistry import KTypeRegistry

from NeutralPatternInput import NeutralPatternInput, PlaneIntersectionAxis
from ProveNeutralPattern import author_document, authored_layouts, checked_file, digest, encode, require, validated_disclosed


PRIOR = "cc798c32cfb5fe20fb59f781da097a2553f8da9e"
AXIS_TAG = "PlaneIntersectionAxis"
CAD_MODULES = {"FreeCAD", "FreeCADGui", "Part", "adsk", "pythoncom", "win32com"}


def points(first, second, start, end, *, units=UnitSystem.KMillimeter):
    definition = PlaneAxis("first-plane", "second-plane", start, end)
    selections = (Selection(definition.FirstPlaneSelectionId, first.name, (SelectPathElem("support_plane", first.id),)),
                  Selection(definition.SecondPlaneSelectionId, second.name, (SelectPathElem("support_plane", second.id),)))
    feature = FeatureStep("axis", "Finite construction axis", FeatureKind.KReference, 0, definition=definition,
                          selection_ids=tuple(pick.id for pick in selections))
    return CadDocument(CadSource("kit-neutral", "<independent axis intent>", "0" * 64),
                       (Configuration("active", "Default", True),), (), (first, second), (), selections,
                       (feature,), (), units=units)


def standalone_inputs():
    first = SupportPlane("first", "Horizontal offset", Transform(SpaceVector(23.0, -9.0, -17.0)))
    right = Transform(SpaceVector(23.0, -9.0, -17.0), SpaceVector(0.0, 0.0, -1.0),
                      SpaceVector(0.0, 1.0, 0.0), SpaceVector(1.0, 0.0, 0.0))
    second = SupportPlane("second", "Vertical offset", right)
    yield "translated", points(first, second, SpaceVector(23.0, 11.0, -17.0), SpaceVector(23.0, -5.0, -17.0))
    normal = sqrt(0.5)
    new_frame = Transform(right.origin, right.x_axis, SpaceVector(-normal, normal, 0.0),
                          SpaceVector(normal, normal, 0.0))
    second = replace(second, transform=new_frame)
    yield "oblique", points(first, second, SpaceVector(21.0, -7.0, -17.0), SpaceVector(27.0, -13.0, -17.0),
                            units=UnitSystem.KInch)


def read_document(raw):
    payload = json.dumps(raw, indent=None, sort_keys=True, ensure_ascii=False)
    from_json = CadDocument.from_json(payload)
    from_mapping = CadDocument.from_dict(raw)
    require(from_json == from_mapping and from_json.to_dict() == raw and from_json.to_json(indent=None) == payload,
            "ordinary document wire did not round trip exactly")
    require(PlaneAxis is history.PlaneAxis is KTypeRegistry[AXIS_TAG] and not from_json.validate(),
            "ordinary public axis identity or document validation changed")
    return from_json


def replace_axis(document, index, definition):
    steps = list(document.feature_timeline)
    steps[index] = replace(steps[index], definition=definition)
    return replace(document, feature_timeline=tuple(steps))


def pattern_bridge(data, document):
    from interchange.serialization.Deserialize import FromData
    from ProjectNeutralPattern import project

    axis = document.feature_timeline[2].definition
    require(type(axis) is PlaneAxis, "normal document read lost the actual typed hinge")
    check = PlaneIntersectionAxis(axis.FirstPlaneSelectionId, axis.SecondPlaneSelectionId, axis.StartMm, axis.EndMm)
    old_document = replace_axis(document, 2, check)
    require(document.to_dict() == old_document.to_dict(), "portable axis altered the scoped proof wire")
    return project(NeutralPatternInput(old_document, FromData(data["output"]), FromData(data["presentation"])))


def preload(mode):
    from interchange.document.Behavior import DocumentIo
    from interchange.document.Validation import DocumentAssemblyValidate, DocumentFeatureValidate, DocumentReferenceValidate
    from interchange.serialization.Deserialize import FromData
    from LocalPatternContainerProcess import audit, linked, observations_with_refusals, verify_keywords
    from convert.adapters.solidworks.Container.Format import KeywordsStream
    from EmitLocalPattern import emit_pattern
    from NeutralPatternInput import register_input_types
    from ProjectNeutralPattern import project

    if mode in ("scope", "binary"):
        register_input_types(with_axis=False)
    for name in ("utf-8", "utf-16-le", "latin-1", "us-ascii"):
        lookup(name)
    return audit, linked, observations_with_refusals, verify_keywords, KeywordsStream, emit_pattern


def worker(mode):
    audit, linked, observe, keywords, keyword_name, emit = preload(mode)
    data = json.load(sys.stdin)
    audit.BeginBuild()
    document = read_document(data["document"] if mode in ("scope", "binary") else data)
    row = {"wire_sha256": digest(document.to_json(indent=None).encode()), "runtime_reads": 0}
    if mode in ("scope", "binary"):
        plan = pattern_bridge(data, document)
        graph, streams, binary = emit(*plan)
        link, headers = linked(binary, streams)
        observed, refused = observe(link, headers, plan)
        keywords(streams[keyword_name], plan, observed)
        require(len(refused) == 9, "scoped archive owner guards changed")
        row.update(container={"sha256": digest(binary), "bytes": len(binary), "version": 4},
                   streams={name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in streams.items()},
                   observed=observed)
    require(not audit.DeniedReads and not {name.split(".")[0] for name in sys.modules} & CAD_MODULES,
            "normal model proof used external data or a CAD runtime")
    if mode == "binary":
        sys.stdout.buffer.write(binary)
    else:
        print(json.dumps(row, sort_keys=True, allow_nan=False))


def execute(mode, data):
    return run((sys.executable, "-I", "-B", str(HERE), "--worker", mode),
               input=encode(data), cwd=ROOT, capture_output=True, timeout=45, check=False)


def passing(mode, data):
    result = execute(mode, data)
    require(result.returncode == 0 and not result.stderr, "guarded neutral axis refused\n" + result.stderr.decode())
    return result.stdout if mode == "binary" else json.loads(result.stdout)


def alter(value, path, change):
    grown = deepcopy(value)
    cursor = grown
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = change
    return grown


def refusals(document):
    raw = document.to_dict()
    step = ("feature_timeline", "$tuple", 0)
    definition = (*step, "definition")
    selection = ("selections", "$tuple", 1, "path")
    first_element = (*selection, "$tuple", 0)
    second_plane = ("support_planes", "$tuple", 1)
    start, end = (ToData(point) for point in (document.feature_timeline[0].definition.StartMm,
                                             document.feature_timeline[0].definition.EndMm))
    checks = (
        ("empty_selection", (*definition, "second_plane_selection_id"), "", "two distinct nonempty selection ids"),
        ("repeated_selection", (*definition, "second_plane_selection_id"), "first-plane", "two distinct nonempty selection ids"),
        ("coincident_tips", (*definition, "end_mm"), start, "distinct endpoints with a finite span"),
        ("nonnumeric_tip", (*definition, "end_mm"), {**end, "z": True}, "finite spatial coordinates"),
        ("endpoint_overflow", (*definition, "end_mm"), {**end, "y": 10**310}, "finite spatial coordinates"),
        ("swapped_feature_roles", (*step, "selection_ids"), {"$tuple": ["second-plane", "first-plane"]}, "inconsistent ordered selection roles"),
        ("wrong_kind", (*step, "kind"), ToData(FeatureKind.KPattern), "requires a reference feature"),
        ("subelement_plane", (*first_element, "subelement"), "edge", "requires a direct support plane selection"),
        ("bad_path", selection, None, "requires a direct support plane selection"),
        ("same_plane_twice", (*first_element, "entity_id"), "first", "must select two distinct support planes"),
        ("absent_plane", (*first_element, "entity_id"), "absent-plane", "selects a missing support plane"),
        ("parallel_planes", (*second_plane, "transform"), ToData(document.support_planes[0].transform), "must define a unique intersection"),
        ("translated_off_line", (*second_plane, "transform", "origin", "x"), 24.0, "endpoints are outside their support planes"),
        ("wrong_axis_direction", (*definition, "end_mm"), {**end, "x": 24.0}, "direction does not follow both support planes"),
    )
    measured = {}
    for name, path, change, reason in checks:
        output = execute("ordinary", alter(raw, path, change))
        require(output.returncode != 0 and not output.stdout and reason in output.stderr.decode(),
                "unexpected public admission or reason for " + name + "\n" + output.stderr.decode())
        measured[name] = reason
    span = alter(alter(raw, (*definition, "start_mm", "y"), 1.7e308), (*definition, "end_mm", "y"), -1.7e308)
    output = execute("ordinary", span)
    reason = "distinct endpoints with a finite span"
    require(output.returncode != 0 and not output.stdout and reason in output.stderr.decode(),
            "two finite coordinates overflowed the representable segment span")
    measured["span_overflow"] = reason
    return measured


def legacy_history(document):
    plate, seed, axis, angle, pattern = document.feature_timeline
    angle = replace(angle, input_feature_ids=(), selection_ids=angle.selection_ids[:1])
    picks = tuple(pick for pick in document.selections if pick.id not in (*axis.selection_ids, "pick/angle-hinge"))
    return replace(document, feature_timeline=(plate, seed, angle, pattern), selections=picks)


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def compare_legacy(document):
    raw = document.to_json(indent=None).encode()
    angled = document.support_planes[-1]
    bad_frame = replace(angled.transform, origin=SpaceVector(2.0, 3.0, 4.0))
    broken = replace(document, support_planes=(*document.support_planes[:-1], replace(angled, transform=bad_frame)))
    source = BytesIO(git("archive", "--format=tar", PRIOR, "src/interchange"))
    method = ("import sys; sys.path.insert(0, sys.argv[1]); "
              "from interchange import CadDocument; "
              "sys.stdout.write(CadDocument.from_json(sys.stdin.read()).to_json(indent=None))")
    with TemporaryDirectory(prefix="KitPlaneAxisPrior-") as temporary, open_tar(fileobj=source) as archive:
        archive.extractall(temporary, filter="data")
        command = (sys.executable, "-I", "-B", "-c", method, str(Path(temporary) / "src"))
        result = run(command, input=raw, cwd=temporary, capture_output=True, timeout=20, check=False)
        refused = run(command, input=broken.to_json(indent=None).encode(), cwd=temporary,
                      capture_output=True, timeout=20, check=False)
    require(result.returncode == 0 and not result.stderr and result.stdout == raw,
            "ordinary historical neutral document bytes changed")
    current = passing("ordinary", document.to_dict())
    require(current["wire_sha256"] == digest(result.stdout), "guarded historical neutral read changed")
    repeated = execute("ordinary", broken.to_dict())
    require(refused.returncode != 0 and repeated.returncode != 0 and not (refused.stdout or repeated.stdout)
            and b"controls disagree with its support frame" in refused.stderr
            and refused.stderr.splitlines()[-1] == repeated.stderr.splitlines()[-1],
            "historical bound plane refusal changed")
    current["historical_invalid_frame_refused"] = True
    return current


def scoped_proof(root):
    packet, models = validated_disclosed(root)
    evidence = {}
    for authored, _ in authored_layouts():
        name = authored["seed"]["name"]
        request = author_document(authored)
        legacy = request.document.feature_timeline[2].definition
        definition = PlaneAxis(legacy.first_plane_selection_id, legacy.second_plane_selection_id, legacy.start_mm, legacy.end_mm)
        document = replace_axis(request.document, 2, definition)
        require(document.to_json() == request.document.to_json(), "portable axis changed the prospective neutral wire")
        data = {"document": document.to_dict(), "output": ToData(request.output), "presentation": ToData(request.presentation)}
        proof = passing("scope", data)
        old = models[name]["original"]
        require(proof["container"] == old["native_container"] and proof["streams"] == old["streams"]
                and proof["observed"] == old["observed"], "normal portable axis changed the proven scoped native graph")
        native = passing("binary", data)
        fixture = "Packet/" + name + ".SLDPRT"
        require(native == checked_file(root, fixture, packet["files"][name + ".SLDPRT"]),
                "normal portable axis changed the measured disclosed native transport")
        evidence[name] = {"container": proof["container"], "typed_streams": len(proof["streams"]),
                          "runtime_reads": proof["runtime_reads"], "wire_sha256": proof["wire_sha256"],
                          "legacy_model": compare_legacy(legacy_history(document))}
    return evidence


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", choices=("ordinary", "scope", "binary"))
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    require(args.disclosed is not None and args.output is not None and not args.output.exists(),
            "use the exact disclosed comparison and a fresh receipt path")
    inputs = dict(standalone_inputs())
    ordinary = {name: passing("ordinary", doc.to_dict()) for name, doc in inputs.items()}
    failed = refusals(inputs["translated"])
    scoped = scoped_proof(args.disclosed.resolve())
    paths = set(git("diff", "--name-only", PRIOR, "--", "src/interchange").decode().splitlines())
    paths.update(("src/interchange/Features/CheckAxisFit.py", "src/interchange/Features/FeaturePlaneAxis.py",
                  "src/interchange/Features/PlaneAxisLine.py", "src/interchange/document/Validation/PlaneAxisValidate.py"))
    receipt = {
        "schema": "kit.portable-plane-intersection-axis.v1",
        "prior_revision": PRIOR, "standalone_axes": ordinary, "refusals": failed,
        "disclosed_pattern_cases": scoped, "new_native_acceptance": 0,
        "guarded_processes": len(ordinary) + len(failed) + 4 * len(scoped),
        "historical_processes": 2 * len(scoped),
        "tools": {path: sha256((ROOT / path).read_bytes()).hexdigest()
                  for path in sorted({*paths, str(HERE.relative_to(ROOT))})},
    }
    with args.output.open("xb") as sink:
        sink.write(encode(receipt))
    print(json.dumps({"receipt_sha256": digest(args.output.read_bytes()), "ordinary_axes": len(ordinary),
                      "refusals": len(failed), "pattern_byte_matches": len(scoped)}, sort_keys=True))


if __name__ == "__main__":
    main()
