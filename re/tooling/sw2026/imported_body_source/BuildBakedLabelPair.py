from base64 import b64decode, b64encode
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import combinations, product
import json
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile


REVISION = "42878d802e4d53ba1dd92528a67fa8122880cff0"
SOURCE_RECEIPT = "re/solidworks/measurements/2026/DisclosedBakedFcstdOwners01.json"
SOURCE_SHA256 = "76471602145cacdac72876f471b00d74cf41397df85ed946e5a719d62afaeb1e"
LOCATOR = r"C:\KitBakedLabelOnly01\Candidate\Baked01.SLDPRT"
EPOCH = 1795300000
ARMS = ("SourceLabel", "LabelOnly")
LABEL_STREAMS = {"Config-0-FeatureBodies/LocalBodies", "Contents/Config-0-ModelHeader",
                 "Contents/Config-0-ResolvedFeatures", "Header2", "swXmlContents/KeyWords"}


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def signature(raw):
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "invalid evidence input")
    raw = path.read_bytes()
    require(signature(raw)["sha256"] == expected, "evidence SHA-256 differs")
    return raw


@contextmanager
def construction_guard():
    active = True

    def audit(event, arguments):
        if active and (event in {"open", "os.scandir", "os.listdir", "os.system", "os.exec", "ctypes.dlopen",
                                "os.fork", "os.forkpty", "subprocess.Popen", "os.posix_spawn"}
                       or event.startswith("socket.")):
            raise PermissionError("model-only construction attempted " + event)

    sys.addaudithook(audit)
    try:
        yield
    finally:
        active = False


def disclosed_inputs(directory, root):
    from AuditBakedFcstdSources import LOCK, NAMES, physical_owner

    evidence = json.loads(checked(root / SOURCE_RECEIPT, SOURCE_SHA256))
    lock = json.loads(checked(directory / "DisclosedSourceLock01.json", LOCK))
    require(evidence["source_lock_sha256"] == LOCK and lock["passed"] is True, "source evidence lacks its live native lock")
    rows = []
    for filename, expected in zip(NAMES, lock["inputs"], strict=True):
        measured = evidence["cases"][filename]
        physical = json.loads(json.dumps(physical_owner(directory / filename, expected)))
        require(measured["source_lock"] == expected and measured["physical_owners"] == physical,
                "literal source and strict owner audit differ")
        strict = measured["strict"]
        require(strict["strict_read"] is True and strict["library_default_material"] is True, "unsupported source background state")
        if expected["standalone_baked"]:
            require(physical["class"] == "Part::Feature" and not physical["driver_lengths_mm"]
                    and strict["admission"] == "unrepresented_source_owners" and strict["feature_kind"] == "imported"
                    and strict["geometry"]["outward_planar_faces"] == 6 and strict["geometry"]["linked_line_carriers"] == 12,
                    "disclosed candidate lacks an actual standalone box owner")
        else:
            require(physical["class"] == "Part::Box" and strict["admission"] == "live_parametric_primitive"
                    and set(physical["driver_lengths_mm"]) == {"Length", "Width", "Height"},
                    "expected a genuinely editable negative control")
        rows.append(measured)
    source, other_label, negative = rows
    physical = source["physical_owners"]
    source_id = source["source_lock"]
    with ZipFile(BytesIO(checked(directory / NAMES[0], source_id["file_sha256"]))) as original:
        xml = fromstring(original.read("Document.xml"))
        visibility = xml.find("./ObjectData/Object/Properties/Property[@name='Visibility']")
        require(visibility is not None and visibility.get("type") == "App::PropertyBool"
                and visibility.find("./Bool").get("value") == "true", "source visibility is outside the fixed ordinary condition")
    target = PureWindowsPath(LOCATOR)
    require(physical["document_label"] == target.stem and physical["label"] != other_label["physical_owners"]["label"],
            "controlled label pair cannot identify one fixed destination and two labels")
    text = {"FreeCAD Source UUID": physical["document_uid"], "FreeCAD Object ID": physical["object_id"],
            "FreeCAD Shape SHA-256": source_id["shape_sha256"]}
    request = {"bounds_mm": source["strict"]["geometry"]["bounds_mm"], "configuration": source["strict"]["configuration"],
               "labels": [physical["label"], other_label["physical_owners"]["label"]], "text": text}
    relation = {"source_sha256": source_id["file_sha256"], "source_shape_sha256": source_id["shape_sha256"],
                "source_shape_member": physical["shape_member"], "source_document_uid": physical["document_uid"],
                "source_object_id": physical["object_id"], "source_local_design_body": source["strict"]["design_body_id"],
                "source_visible": True,
                "negative_control_sha256": negative["source_lock"]["file_sha256"], "negative_control_rejected": True}
    return request, relation


def computed_box(bounds, name):
    from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.Transform import KTransformIdentity
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordSource import CadSource

    (left, right), (front, back), (z0, z1) = bounds
    loop = tuple(PlaneVector(x, y) for x, y in ((left, front), (right, front), (right, back), (left, back)))
    segments = tuple(LineGeometry(a, b) for a, b in zip(loop, loop[1:] + loop[:1], strict=True))
    raw, *_ = BuildPrism("label-contrast", KTransformIdentity, segments, z0, z1)
    body, = raw.bodies
    model = replace(raw, bodies=(replace(body, design_body_id=""),))
    return CadDocument(CadSource("kit.neutral", "", ""), (Configuration("active", name, True),),
                       (), (), (), (), (), (), brep=model)


def linked_replay(archive, link):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut

    version = link.ConfigValue.VersionValue
    graph = link.ResolvedValue
    cfg, inherited = WriteConfigMut(link.ConfigValue.RootValue, version, link.ConfigValue.HeaderValue)
    raw, resolved = WriteResolMut(graph.RootsValue, graph.ExtraFields, version, inherited.MapValue, graph.ContextValue)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), version)
    result = {link.ConfigName: cfg, link.StreamName: raw, "Contents/CMgr": WriteCmgrMut(manager.RootValue, version)}
    for key in ("Header2", "Contents/Config-0-ModelHeader"):
        result[key] = WriteHeadGraph(ReadHeaderGraph(archive.require(key), version), version)
    require(all(data == archive.require(name) for name, data in result.items())
            and inherited.MapValue.CounterValue == graph.MapBase and resolved.MapValue.CounterValue == graph.MapValue.CounterValue,
            "typed archive replay lost its field data or shared maps")
    return result


def verify_box(document, bounds, body):
    from convert.Geometry.Parasolid import KLengthScale
    from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import KMillimetersPerMeter
    from convert.adapters.solidworks.Core.Partition.PartMass import PlanarMoments
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from math import dist, isclose, prod

    model = document.brep
    solid, = model.bodies
    points = {vertex.id: (vertex.point.x, vertex.point.y, vertex.point.z) for vertex in model.vertices}
    axes = tuple(zip(*points.values(), strict=True))
    actual = tuple((min(axis), max(axis)) for axis in axes)
    expected = tuple(tuple((value / KMillimetersPerMeter) / KLengthScale for value in axis) for axis in bounds)
    require(solid.design_body_id == body.id and actual == expected and len(model.faces) == 6
            and len(model.edges) == 12 and len(model.vertices) == 8, "strict target solid differs from the computed box")
    corners = set(product(*expected))
    actual_edges = {frozenset((points[edge.start_vertex_id], points[edge.end_vertex_id])) for edge in model.edges}
    expected_edges = {frozenset(pair) for pair in combinations(corners, 2)
                      if sum(a != b for a, b in zip(*pair, strict=True)) == 1}
    require(set(points.values()) == corners and actual_edges == expected_edges, "strict target box incidence differs")
    baseline = tuple(low for low, _ in expected)
    volume, *moments = PlanarMoments(model, SpaceVector(*baseline))
    center = tuple(low + moment / volume for low, moment in zip(baseline, moments, strict=True))
    require(isclose(volume, prod(high - low for low, high in bounds), rel_tol=1e-14)
            and dist(center, tuple((low + high) / 2 for low, high in bounds)) <= 1e-12,
            "target signed mass differs from the computed box")
    margin = max(abs(a-b) for pair, original in zip(actual, bounds, strict=True) for a, b in zip(pair, original, strict=True))
    return {"bounds_mm": actual, "volume_mm3": volume, "center_mm": center, "design_body_id": body.id,
            "maximum_unit_roundtrip_residual_mm": margin}


def verify_target(candidate, label, request):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
    from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KLocalBodyStream, KPartitionStream
    from convert.adapters.solidworks.Core.Properties.ReadPartText import ReadPartText
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import ReadLocalOwner
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import ReadLocalWrap
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import ReadLocalPay
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    require(archive.streams == candidate.StreamsValue, "container changed generated streams")
    for key in ("Header2", "Contents/Config-0-ModelHeader"):
        require(ReadHeader(archive.require(key), 19000).SelfFile.PathValue == LOCATOR, "target self identity differs")
    document = open_document(candidate.BytesValue, source_format="solidworks.sldprt")
    document.assert_valid()
    body, = document.bodies
    (feature,) = (step for step in document.feature_timeline if step.kind.value == "imported")
    config, = document.configurations
    payload, mark = ReadLocalPay(document.brep_payloads, archive.require(KPartitionStream))
    group = ReadLocalWrap(archive.require(KLocalBodyStream), payload)
    link = ReadNativeLink(archive, 0)
    atom_node, feature_id = ReadLocalOwner(link, group, mark)
    atom = atom_node.FieldsValue
    proof = document.metadata["solidworks.native_body_names"]
    require(group == proof["storage_key"] == feature.name == body.name == label and proof["status"] == "complete"
            and proof["name_owner"] == "local_storage_key" and proof["complete_brep_binding"] is True
            and feature.id == body.final_feature_id == f"sldprt:feature:{feature_id}"
            and proof["last_modifying_feature_id"] == feature_id and candidate.AtomId == atom["f140"] == proof["atom_manager_id"]
            and atom["f18"] is None and config.name == request["configuration"] and config.active and not feature.suppressed,
            "BaseBody, local group and actual managed atom disagree")
    replay = linked_replay(archive, link)
    nodes, _ = ReadLocalNodes(payload)
    ordered = tuple(nodes[index] for index in sorted(nodes))
    require(EncodeLocalBody(label, ordered) == archive.require(KLocalBodyStream), "typed local body replay changed the envelope")
    text = ReadPartText(document, archive)
    require(text.DocumentFields == request["text"] and not text.SummaryFields and not text.ConfigFields,
            "native document text belongs to the wrong owner")
    return {"feature_label": label, "document_self": LOCATOR, "configuration": config.name,
            "feature_id": feature_id, "atom_id": atom["f140"], "active_mark": mark,
            "body_name_owner": proof["name_owner"], "document_text": dict(text.DocumentFields),
            "atom_scope_words": {key: atom.get(key) for key in ("f140", "f170", "f188", "f18c")},
            "geometry": verify_box(document, tuple(map(tuple, request["bounds_mm"])), body),
            "part": signature(candidate.BytesValue), "kernel": signature(payload),
            "linked_replay_streams": sorted((*replay, KLocalBodyStream)),
            "streams": {name: signature(data) for name, data in archive.streams.items()}}


def build_pair(sdk, request):
    sys.path.insert(0, str(sdk))
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
    from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
    from convert.adapters.solidworks.Core.Preparation.Imports.ImportPartPlan import ImportPartPlan
    from convert.adapters.solidworks.Core.Preparation.Imports.MakeImportLight import MakeImportLight
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(codec)
    with construction_guard():
        document = computed_box(request["bounds_mm"], request["configuration"])
        inputs = PartTextInput({}, request["text"], {})
        light = MakeImportLight(EPOCH)
        candidates = []
        for label in request["labels"]:
            plan = ImportPartPlan(PureWindowsPath(LOCATOR).stem, request["configuration"], label)
            recipe = replace(MakePartRecipe(plan, EPOCH), OutputValue=SelfFileInput(LOCATOR, EPOCH), PropertiesValue=inputs)
            candidates.append(MakeBareImport(document, recipe, plan, AmbientValue=light))
    cases = [verify_target(candidate, label, request) for candidate, label in zip(candidates, request["labels"], strict=True)]
    baseline, contrast = cases
    for key in ("atom_scope_words", "feature_id", "atom_id", "active_mark", "geometry", "kernel", "document_self", "configuration", "document_text"):
        require(baseline[key] == contrast[key], "feature label changed an independent target owner")
    require(baseline["feature_label"] != contrast["feature_label"] and baseline["part"] != contrast["part"], "label-only contrast has no effect")
    left, right = (case["streams"] for case in cases)
    require(left.keys() == right.keys() and left["docProps/custom.xml"] == right["docProps/custom.xml"],
            "label-only contrast changed the separate identity text stream")
    changed = {key for key in left if left[key] != right[key]}
    require(changed == LABEL_STREAMS, "label-only contrast changed an unqualified stream")
    return {"cases": dict(zip(ARMS, cases, strict=True)), "changed_streams": sorted(changed),
            "runtime_input_reads": 0, "parts": [b64encode(candidate.BytesValue).decode() for candidate in candidates]}


def main(source, output):
    output = output.resolve()
    require(output.is_absolute() and not output.exists() and not any((parent / ".git").exists() for parent in output.parents),
            "keep generated candidates in a fresh external directory")
    root = Path(__file__).resolve().parents[4]
    request, relation = disclosed_inputs(source.resolve(strict=True), root)
    with TemporaryDirectory(prefix="kit-baked-label-") as scratch:
        data = check_output(("git", "-C", str(root), "archive", "--format=tar", REVISION, "src"))
        with open_tar(fileobj=BytesIO(data)) as sdk:
            sdk.extractall(scratch, filter="data")
        captures = []
        for _ in range(2):
            result = run((sys.executable, "-I", "-B", __file__, "--worker", str(Path(scratch) / "src")),
                         input=json.dumps(request), capture_output=True, text=True, cwd=scratch, timeout=120)
            require(result.returncode == 0, result.stderr)
            captures.append(json.loads(result.stdout))
        require(captures[0] == captures[1], "independent model-only constructions differ")
    ready = captures[0]
    output.mkdir()
    for arm, payload in zip(ARMS, ready.pop("parts"), strict=True):
        blob = b64decode(payload, validate=True)
        require(signature(blob) == ready["cases"][arm]["part"], "candidate identity differs")
        with (output / (arm + ".SLDPRT")).open("xb") as stream:
            stream.write(blob)
    receipt = {"schema": "kit.freecad.disclosed-baked-label-pair.v1", "sdk_revision": REVISION,
               "source_owner_audit_sha256": SOURCE_SHA256, "source_relation": relation, "author_epoch": EPOCH,
               "geometry_only_target_projection": True, "intact_source_qualified": False,
               "registry_enabled": False, "heldout_inputs_read": 0, "native_processes_started": 0,
               "independent_host_processes": 2, **ready}
    with (output / "Receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "--worker":
        print(json.dumps(build_pair(Path(sys.argv[2]), json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        main(Path(sys.argv[1]), Path(sys.argv[2]))
