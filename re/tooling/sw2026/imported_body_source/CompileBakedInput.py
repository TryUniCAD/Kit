from argparse import ArgumentParser
from contextlib import contextmanager
from codecs import lookup
from dataclasses import dataclass, replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import json
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
from convert.adapters.solidworks.Core.Preparation.Imports.MakeImportLight import MakeImportLight
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

BASIS = "660100bffe19eb22795c34006516feb369286674"
EPOCH = 1795300000
GUEST_DIR = PureWindowsPath(r"C:\KitBakedToleranceNative01") / "Candidates"
MEASURED = {
    "Baked01": (9910, "5b4100d6c7f9b2e172337ced9c6c1d882dcac505ee8577414e8258c6028c9e83"),
    "Baked02": (9895, "448f35575f79d58e3154eba0f54d2eb151a2c6c2b0b23d1feb1126c6fffa8efc"),
}


@dataclass(frozen=True)
class BakedProjection:
    request: object
    plan: object
    source_capabilities: frozenset
    modeled_native_capabilities: frozenset
    dropped_capabilities: frozenset
    source: dict
    boundary: dict


def require(predicate, detail):
    if not predicate:
        raise ValueError(detail)


def digest(data):
    return sha256(data).hexdigest()


@contextmanager
def construction_guard():
    active = True
    def audit(event, args):
        if not active:
            return
        if event == "open" or event.startswith("socket.") or event in (
            "subprocess.Popen", "os.system", "os.posix_spawn", "os.exec",
        ):
            raise ValueError("source proof attempted external access: " + event)
        if event == "import" and str(args[0]).split(".")[0].casefold() in {
            "win32com", "pythoncom", "freecad", "freecadgui", "part", "sketcher",
        }:
            raise ValueError("source proof attempted a CAD runtime import")
    sys.addaudithook(audit)
    try:
        yield
    finally:
        active = False


def read_graph(document, archive):
    from convert.adapters.freecad.BodyLineage.BoxShapeOwner import FindShapeData, ReadShapeNodes
    from convert.adapters.freecad.Native import ElemData, NativeObjectA

    feature, = document.feature_timeline
    owner, = archive.objects
    declaration, = archive.root.findall("./Objects/Object")
    dependency, = archive.root.findall("./Objects/ObjectDeps")
    require(archive.root.tag == "Document"
            and archive.root.get("SchemaVersion") == "4" and archive.root.get("FileVersion") == "1"
            and archive.root.get("ProgramVersion") == "1.1R20260928 (Git shallow)"
            and declaration.get("name") == owner.name and declaration.get("id") == owner.object_id
            and declaration.get("type") == owner.type_id == "Part::Feature"
            and dependency.attrib == {"Name": owner.name, "Count": "0"} and not len(dependency)
            and not owner.dependencies and not owner.extensions and not owner.touched
            and feature.definition.object_data == NativeObjectA(owner)
            and feature.attributes["freecad"] == NativeObjectA(owner),
            "source has edited, dependent, alternate or unbound feature ownership")
    transients = tuple(ElemData(row) for row in owner.transient_properties)
    if transients:
        require(len(transients) == 1 and transients[0]["tag"] == "_Property"
                and transients[0]["attributes"].get("name") == "_ElementMapVersion"
                and transients[0]["attributes"].get("type") == "App::PropertyString"
                and set(transients[0]) == {"tag", "attributes"},
                "source carries other transient semantic owners")
    require(set(owner.properties) == {
        "ExpressionEngine", "Label", "Label2", "Placement", "Shape", "ShapeMaterial", "Visibility",
    }, "source has a link, driver, proxy or unknown persistent owner")
    shape, nodes = ReadShapeNodes(owner)
    require([node.tag for node in nodes] == ["Part", "ElementMap"]
            and set(nodes[0].attrib) == {"ElementMap", "file"}
            and nodes[0].get("ElementMap") == "15.70200.5"
            and not nodes[1].attrib and not len(nodes[1]) and not (nodes[1].text or "").strip(),
            "source has populated, alternate or unqualified persistent element names")
    hashers = archive.root.findall("./StringHasher")
    require(len(hashers) == 1 and hashers[0].attrib == {"saveall": "0", "threshold": "0", "count": "0"} and not len(hashers[0])
            and not (hashers[0].text or "").strip(), "source has nonempty native string owners")
    (placement,) = owner.properties["Placement"].findall("./PropertyPlacement")
    require(tuple(float(placement.get(key)) for key in ("Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3"))
            == (0., 0., 0., 0., 0., 0., 1.), "source has an independent nonidentity placement")
    expression, = owner.properties["ExpressionEngine"].findall("./ExpressionEngine")
    require(expression.attrib == {"count": "0"} and not len(expression), "source carries an owned expression")
    part = nodes[0]
    selected = FindShapeData(document, archive, owner, shape, part, "feature_id", feature.id)
    require(not selected.attributes.get("freecad_sidecars")
            and feature.attributes["brep_payload_ids"] == [selected.id],
            "source shape carries alternate geometry or sidecar data")
    return owner, selected


def check_properties(document, archive, owner):
    from convert.adapters.freecad.Native import NativeObjectA
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxMat import ReadBoxMat
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import KDefaultMat
    from interchange import ValueKind

    feature, = document.feature_timeline
    require(ReadBoxMat(NativeObjectA(owner)["properties"]) == KDefaultMat,
            "source has an unrepresented physical material or appearance")
    fields = {parameter.attributes["freecad_path"]: parameter for parameter in document.parameters}
    require(len(fields) == len(document.parameters) == 3 and set(fields) == {"Label", "Label2", "Visibility"}
            and all(parameter.owner_id == feature.id and parameter.expression is None and not parameter.value.unit
                    for parameter in fields.values()), "source carries an unaccounted edit or driver")
    label = owner.properties["Label"].find("./String").attrib["value"]
    require(feature.name == label and label.strip() and label.isprintable()
            and fields["Label"].value.kind is ValueKind.STRING and fields["Label"].value.value == label
            and fields["Label2"].value.kind is ValueKind.STRING and fields["Label2"].value.value == ""
            and fields["Visibility"].value.kind is ValueKind.BOOLEAN and fields["Visibility"].value.value is True,
            "source label, secondary text or visibility is outside the proven scope")
    rows = archive.root.findall("./Properties/Property")
    properties = {row.attrib["name"]: row for row in rows}
    require(len(rows) == len(properties) == 17 and set(properties) == {
        "Comment", "Company", "CreatedBy", "CreationDate", "Id", "Label", "LastModifiedBy",
        "LastModifiedDate", "License", "LicenseURL", "Material", "Meta", "ShowHidden", "TipName",
        "Uid", "UnitSystem", "UseHasher",
    }, "source has unclassified document-level semantic owners")
    require(properties["Material"].find("./Map").attrib == {"count": "0"}
            and properties["Meta"].find("./Map").attrib == {"count": "0"}
            and properties["TipName"].find("./String").attrib == {"value": ""}
            and properties["ShowHidden"].find("./Bool").attrib == {"value": "false"},
            "document carries other material, feature or display state")
    title = properties["Label"].find("./String").attrib["value"]
    require(title.strip() and title.isprintable(), "source document title is inadmissible")
    return title, label, properties["Uid"].find("./Uuid").attrib["value"]


def compare_native_view(document, raw, pair):
    from convert.adapters.freecad.Native import ReadNativeFcstd

    replay = ReadNativeFcstd(raw, RecordReplay=True)
    stream_names = {part.id: part.source_stream for part in replay.brep_payloads}
    pair_ids = frozenset(part.id for part in pair)
    expected_name = Path(document.source.path).name if document.source.path else "Document.FCStd"
    require(all(part.source_stream == expected_name for part in pair), "source path does not name its bound archive owners")
    canonical = replace(
        document, source=replace(document.source, path=""),
        brep_payloads=tuple(replace(part, source_stream=stream_names[part.id])
                            if part.id in pair_ids else part for part in document.brep_payloads),
    )
    require(canonical == replay, "supplied neutral view differs from its complete immutable FCStd archive")


def make_projection(document, boundary, config):
    from BuildBakedLabelPair import computed_box
    from ProveBakedLocalTolerance import ring_signature
    from convert.adapters.solidworks.Archive.Construction.Part.Imports.CheckBareImport import ReadBareModel
    from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadBareConfig import ReadBareConfig
    from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismSolid import CheckPrismSolid
    from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadBoxTolerance import ReadBoxTol
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings

    groups = boundary["tolerances_mm"]
    unique = {tolerance for values in groups.values() for tolerance in values}
    require(len(unique) == 1 and all(len(values) == 1 for values in groups.values()),
            "source tolerance has no single measured rule for all 26 boundary owners")
    (value,) = unique
    request = computed_box(boundary["bounds_mm"], config)
    model = request.brep
    canonical = replace(model, **{group: tuple(replace(row, tolerance=value) for row in getattr(model, group))
                                 for group in groups})
    request = replace(request, brep=canonical)
    request.assert_valid()
    require(ring_signature(ReadMassRings(document.brep)) == ring_signature(ReadMassRings(canonical)),
            "regenerated model changed an outward source ring or its direction")
    require(ReadBareModel(request) == canonical and ReadBareConfig(request).name == config,
            "regenerated geometry does not enter the exact shared bare-model prerequisites")
    CheckPrismSolid(canonical, AllowTolerance=True)
    tolerance_m = ReadBoxTol(canonical)
    return request, tolerance_m


def prove_baked(document):
    from AuditBakedFcstdSources import boundary_summary
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
    from convert.adapters.freecad.Native import ArchiveMembers, LoadNative
    from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
    from convert.adapters.solidworks.Core.Preparation.Imports.ImportPartPlan import ImportPartPlan
    from interchange.Enums.EnumDocument import Capability
    from interchange.Enums.EnumFeatures import FeatureKind
    from interchange.Features.FeatureKinds import NativeFeature

    require(document.source.format_id == "freecad.fcstd" and document.units == "mm"
            and document.schema_version == "1.0" and document.assembly is None and document.DrawingValue is None
            and len(document.feature_timeline) == len(document.bodies) == len(document.configurations) == 1
            and document.brep is not None and not (document.sketches or document.support_planes
                or document.selections or document.materials or document.meshes or document.diagnostics),
            "requires one complete standalone imported FreeCAD geometry owner")
    feature, = document.feature_timeline
    require(feature.kind is FeatureKind.KImported and type(feature.definition) is NativeFeature
            and feature.definition.format_id == "freecad.fcstd"
            and feature.definition.type_id == "Part::Feature"
            and not (feature.input_feature_ids or feature.sketch_id or feature.selection_ids or feature.suppressed)
            and feature.operation is None, "source is not a literal nonparametric Part::Feature")
    (config,), (body,), (shape_body,) = document.configurations, document.bodies, document.brep.bodies
    require(config.active and config.parent_id is None and not (config.overrides or config.suppressed_feature_ids
            or config.attributes) and body.attributes == {"freecad_generated": True}
            and not body.material_id and body.final_feature_id == feature.id and shape_body.design_body_id == body.id,
            "imported solid is detached from its actual generated design body or active configuration")
    document.assert_valid()
    pair = NativeDocPair(document)
    require(pair is not None and type(pair[0].data) is bytes and pair[0].sha256 == document.source.sha256,
            "unbound or ambiguous native archive digest")
    raw = pair[0].data
    archive = LoadNative(raw)
    owner, shape = read_graph(document, archive)
    require(len(document.brep_payloads) == 3 and {part.id for part in document.brep_payloads} ==
            {pair[0].id, pair[1].id, shape.id}
            and shape_body.attributes == {"brep_payload_id": shape.id, "feature_id": feature.id},
            "missing actual sole Shape payload / decoded solid / imported producer join")
    zipped, members = ArchiveMembers(raw)
    with zipped:
        require(set(members) == {"Document.xml", shape.source_stream},
                "the archive has another body, appearance or sidecar owner")
    title, label, uid = check_properties(document, archive, owner)
    compare_native_view(document, raw, pair)
    boundary = boundary_summary(document.brep, body.id)
    request, tolerance = make_projection(document, boundary, config.name)
    transferred = frozenset({Capability.KBrep, Capability.KConfigurations, Capability.KBodyStructure})
    dropped = frozenset({Capability.KNativePayloads, Capability.KParameters,
                         Capability.KProvenance, Capability.KRoundtripMeta})
    require(GetDocumentCaps(document) == transferred | dropped, "source has an unaccounted capability")
    plan = ImportPartPlan(title, config.name, label)
    source = {"archive_sha256": pair[0].sha256, "document_xml_sha256": digest(archive.document_xml),
              "shape_sha256": shape.sha256, "shape_member": shape.source_stream, "document_uid": uid,
              "object_name": owner.name, "object_id": owner.object_id, "feature_id": feature.id,
              "design_body_id": body.id, "configuration_id": config.id, "label": label, "title": title,
              "authored_parameters": [part.attributes["freecad_path"] for part in document.parameters],
              "active_configuration": config.name, "tolerance_m": tolerance,
              "element_map_rows": 0, "source_history_present": False}
    return BakedProjection(request, plan, GetDocumentCaps(document), transferred, dropped, source, boundary)



def compose_baked(projection, locator, epoch):
    path = PureWindowsPath(locator)
    require(path.is_absolute() and path.suffix.casefold() == ".sldprt", "target requires an absolute SLDPRT locator")
    recipe = replace(MakePartRecipe(projection.plan, epoch), OutputValue=SelfFileInput(str(path), epoch))
    return MakeBareImport(
        projection.request, recipe, projection.plan, AmbientValue=MakeImportLight(epoch), AllowBoxTolerance=True
    )


def label_set(values):
    return sorted(value.value for value in values)


def main():
    parser = ArgumentParser()
    parser.add_argument("sources", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(not check_output(["git", "diff", "--name-only", BASIS, "--", "src"], cwd=ROOT),
            "the shared SDK differs from the measured revision")
    for encoding in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(encoding)
    from convert import open_document
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps

    measured = ROOT / "re/solidworks/measurements/2026/DisclosedBakedFcstdOwners01.json"
    authority = measured.read_bytes()
    require(digest(authority) == "76471602145cacdac72876f471b00d74cf41397df85ed946e5a719d62afaeb1e",
            "original source ownership evidence changed")
    pins = json.loads(authority)["cases"]
    cases = {}
    disclosures = {}
    for name in ("Baked01.FCStd", "Baked02.FCStd", "ParametricControl.FCStd"):
        path = args.sources / name
        require(path.is_file() and not path.is_symlink(), "expected an immutable disclosed source")
        raw = path.read_bytes()
        require(digest(raw) == pins[name]["source_lock"]["file_sha256"], "disclosed physical source changed")
        path_doc = open_document(path, source_format="freecad.fcstd", strict=True)
        stream_doc = open_document(BytesIO(raw), source_format="freecad.fcstd", strict=True)
        if not pins[name]["source_lock"]["standalone_baked"]:
            try:
                prove_baked(path_doc)
            except ValueError as error:
                require(str(error) == "source is not a literal nonparametric Part::Feature",
                        "wrong parametric control refusal")
                cases[name] = {"refused": str(error), "capabilities": label_set(GetDocumentCaps(path_doc)),
                               "drivers": sorted(parameter.attributes["freecad_path"] for parameter in path_doc.parameters
                                                 if parameter.value.unit == "mm")}
            else:
                raise ValueError("live parametric box unexpectedly entered the fallback")
            continue
        stem = Path(name).stem
        initial = prove_baked(path_doc)
        target = str(GUEST_DIR / (stem + ".SLDPRT"))
        disclosures[name] = path_doc
        with construction_guard():
            repeated = prove_baked(path_doc)
            from_stream = prove_baked(stream_doc)
            composed = compose_baked(repeated, target, EPOCH)
            alternate = compose_baked(from_stream, target, EPOCH)
        require(initial == repeated == from_stream, "the source proof changes with replay or source transport")
        obtained = (len(composed.BytesValue), digest(composed.BytesValue))
        require(obtained == MEASURED[stem] and composed.BytesValue == alternate.BytesValue,
                f"intact source did not reproduce the measured native candidate: {obtained}")
        cases[name] = {"target": {"locator": target, "size": obtained[0], "sha256": obtained[1],
                                  "streams": {key: digest(value) for key, value in composed.StreamsValue.items()}},
                       "source": initial.source, "boundary": initial.boundary,
                       "source_capabilities": label_set(initial.source_capabilities),
                       "modeled_native_capabilities": label_set(initial.modeled_native_capabilities),
                       "projected_untransferred_capabilities": label_set(initial.dropped_capabilities),
                       "target_payload_count": len(initial.request.brep_payloads),
                       "projected_request_sha256": digest(initial.request.to_json(indent=None).encode()),
                       "guarded_read_events": 0, "path_and_stream_equivalent": True}
    edited = replace(path_doc, source=replace(path_doc.source, format_id="kit.neutral"))
    try:
        prove_baked(edited)
    except ValueError as error:
        require(str(error) == "requires one complete standalone imported FreeCAD geometry owner",
                "wrong cross-format or opaque relabel refusal")
    else:
        raise ValueError("source relabeling unexpectedly granted fallback authority")
    source = disclosures["Baked01.FCStd"]
    changed = replace(source.brep, faces=tuple(replace(face, tolerance=2e-7) for face in source.brep.faces))
    stale_view = replace(source, brep=changed)
    try:
        with construction_guard():
            prove_baked(stale_view)
    except ValueError as error:
        require(str(error) == "supplied neutral view differs from its complete immutable FCStd archive",
                "stale geometry refused outside its native source binding")
        stale_refusal = str(error)
    else:
        raise ValueError("altered neutral geometry unexpectedly passed the intact-source proof")
    report = {
        "schema": "kit.sw2026.baked-import-projection.v1", "sdk_revision": BASIS,
        "source_authority_sha256": digest(authority), "creation_epoch": EPOCH,
        "cases": cases, "altered_brep_refused": stale_refusal, "relabeled_source_refused": True,
        "exact_generated_candidates": 2, "target_files_written": 0, "heldout_credit": 0,
        "native_launches": 0, "new_native_acceptance": 0, "fcstd_conversion_credit": 0,
    }
    data = (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"sha256": digest(data), "exact_generated_candidates": 2}, sort_keys=True))


if __name__ == "__main__":
    main()
