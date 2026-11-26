from argparse import ArgumentParser
from dataclasses import replace
from pathlib import Path, PureWindowsPath
from struct import pack
from subprocess import check_output
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "re/automation"), str(ROOT / "re/solidworks/EncoderBoundary"),
                str(ROOT / "re/solidworks/RendererBoundary"), str(ROOT / "re/solidworks/WriterResearch")]

from EncoderRoundTrip.Artifacts import DOCUMENT_LIMIT, canonical_json, digest, read_record, write_artifact
from InspectResavedRenderer import REVISION, demand, guarded, verify_dependency
from ReplayEmptyAppearance import REQUEST_LIMIT, VERSION, inspect_generated, read_bounded, read_owner

PROPERTY_REVISION = "5fb7e7737f0b9af52373da5e3f4556cd83ba8607"
PART_SCHEMA = "kit.research.exact-sketch-presentation.v1"
DEFINITION = "Contents/Definition"
PROPERTIES = "Contents/CusProps"


def check_dependencies(sdk, property_root):
    verify_dependency(sdk)
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=property_root).decode().strip()
    changes = check_output(("git", "status", "--porcelain", "--untracked-files=no"), cwd=property_root)
    demand(revision == PROPERTY_REVISION and not changes, "expected the pinned property research checkout")
    for root, path in ((sdk, "src"), (property_root, "re/solidworks/PropertyBoundary")):
        untracked = check_output(("git", "ls-files", "--others", "--exclude-standard", "--", path), cwd=root)
        demand(not untracked, "dependency subtree contains untracked files")


def initialize(sdk, property_root):
    sdk, property_root = sdk.resolve(), property_root.resolve()
    check_dependencies(sdk, property_root)
    import convert
    import interchange
    demand(all(Path(module.__file__).resolve().is_relative_to(sdk / "src")
               for module in (convert, interchange)), "SDK packages escaped the pinned checkout")
    sys.path.insert(0, str(property_root / "re/solidworks/PropertyBoundary"))
    import EmptyCutPropertyOwner
    demand(Path(EmptyCutPropertyOwner.__file__).resolve() ==
           property_root / "re/solidworks/PropertyBoundary/EmptyCutPropertyOwner.py",
           "property implementation escaped the pinned checkout")
    from codecs import lookup
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    return EmptyCutPropertyOwner


def check_imports(sdk, property_root):
    paths = {
        "ComposeTopAnnotation": ROOT / "re/solidworks/WriterResearch/ComposeTopAnnotation.py",
        "ExactSketchIntent": ROOT / "re/solidworks/EncoderBoundary/ExactSketchIntent.py",
        "ReplayEmptyAppearance": ROOT / "re/solidworks/RendererBoundary/ReplayEmptyAppearance.py",
        "EmptyCutPropertyOwner": property_root / "re/solidworks/PropertyBoundary/EmptyCutPropertyOwner.py",
    }
    for name, path in paths.items():
        demand(Path(sys.modules[name].__file__).resolve() == path, f"{name} escaped its expected checkout")
    for name, module in tuple(sys.modules.items()):
        if name.split(".", 1)[0] in ("convert", "interchange") and getattr(module, "__file__", None):
            demand(Path(module.__file__).resolve().is_relative_to(sdk / "src"), f"{name} escaped the SDK pin")


def part_request(raw):
    from ComposeTopAnnotation import REQUEST_SCHEMA, read_request

    value = read_record(raw)
    demand(set(value) == {"schema", "document", "display_units", "annotation_view", "show_construction_planes"}
           and value["schema"] == PART_SCHEMA and value["display_units"] == "mm"
           and type(value["show_construction_planes"]) is bool and canonical_json(value) == raw,
           "expected canonical exact sketch, Top and construction-plane intent")
    document, top = read_request(canonical_json({"schema": REQUEST_SCHEMA, "document": value["document"],
                                                  "annotation_view": value["annotation_view"]}))
    configuration, = document.configurations
    demand(configuration.active is True and configuration.id == top.configuration_id,
           "Top annotation must bind the active neutral configuration")
    return document, top, value["show_construction_planes"]


def compose(document, top, flag, locator, epoch, appearance, present, props):
    from ComposeTopAnnotation import add_top_annotation
    from ExactSketchIntent import make_mm_view, validate_si_plan
    from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
    from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
    from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
    from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeAppearMgr import MakeAppearMgr
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Container.Container import BuildSldprt
    from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath

    def construct():
        plan = validate_si_plan(document)
        mm = make_mm_view(document)
        PlanPartWrite(mm)
        target = RequirePartPath(locator, epoch)
        recipe = MakePartRecipe(plan, epoch)
        demand(not recipe.DefinitionValue.DisplayBits, "plane intent requires the fresh generated Definition")
        definition = replace(recipe.DefinitionValue, DisplayBits=(17,) if flag else ())
        inputs = BindPartIntent(mm, plan, replace(recipe, DefinitionValue=definition), target)
        CheckPartInput(mm, inputs, plan)
        allocator = PersistentIds()
        system = MakePartBaseMut(inputs, plan, allocator)
        add_top_annotation(system.RootValue, top)
        profile = MakePartProfMut(system, inputs, plan, allocator)
        candidate = FinishBlindMut(system, profile, inputs, plan, allocator)
        fields = candidate.DefinitionValue.DocumentValue.FieldsValue
        demand(fields.get("has_pwmaterial") == 0 and "f1110" not in fields,
               "generated Definition does not have a fresh appearance slot")
        fields.update(MakeAppearMgr(appearance))
        graph_wire = WriteModelDef(candidate.DefinitionValue).OutputValue
        binary, xml, property_state = props.manufacture(present)
        streams = dict(candidate.StreamsValue)
        demand(not streams.keys() & ({PROPERTIES} | xml.keys()), "generated part already owns property streams")
        streams.update({DEFINITION: graph_wire, PROPERTIES: binary, **xml})
        return candidate, mm, BuildSldprt(streams, FormatVersion=4), streams, property_state

    return guarded(construct)


def read_configuration(mm, public_document, top, archive, link):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrRows import ReadCmgrRows
    from convert.adapters.solidworks.Container.Format import KeywordsStream
    from convert.adapters.solidworks.Core.Native import ParseKeywords
    from convert.adapters.solidworks.Core.Properties.ReadConfigProps import ReadConfigProps
    from convert.adapters.solidworks.Core.Reading.ReadAdapter import ConfigId
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName

    configuration, = mm.configurations
    observed, = public_document.configurations
    demand(observed.id == configuration.id == top.configuration_id == ConfigId(0)
           and observed.name == configuration.name and observed.active is True and link.ConfigName == "Contents/Config-0",
           "physical and neutral configuration identities differ")
    cmgr = ReadCmgrMut(archive.Require("Contents/CMgr"), VERSION).RootValue
    row, = ReadCmgrRows(cmgr)
    keywords, _ = ParseKeywords(archive.Require(KeywordsStream))
    keyword, = keywords
    demand(cmgr.FieldsValue["f360"] is row is cmgr.FieldsValue["f368"]
           and row.FieldsValue["f08"] == row.FieldsValue["f0c"] == keyword.configuration_id == 0
           and keyword.properties.get("id") == "0"
           and ReadNativeName(row) == keyword.properties.get("Name") == configuration.name,
           "native CMgr aliases and explicit keyword row disagree")
    demand(ReadConfigProps(public_document, archive, VERSION) == {0: {}},
           "empty configuration XML does not bind the actual directory row")
    return {"id": 0, "name": configuration.name, "config_xml_owner_verified": True}


def read_geometry(candidate, document, mm, top, flag, archive, link):
    from ComposeTopAnnotation import ANNOTATION_CLASS, annotation_matrix
    from ExactSketchIntent import lines, point_words
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.BuildPrismGeom import BuildPrismGeom
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismPlan import ReadPrismBody
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import ReadLineLoop
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude

    graph, resolved = link.ConfigValue, link.ResolvedValue
    fields = graph.RootValue.FieldsValue
    retained = {entry.IndexValue: entry.EntryValue for entry in resolved.MapValue.EntriesValue}
    demand(resolved.MapBase == graph.MapValue.CounterValue == candidate.ConfigValue.MapValue.CounterValue
           and resolved.MapValue.CounterValue == candidate.ResolvedValue.MapValue.CounterValue
           and all(retained.get(entry.IndexValue) is entry.EntryValue for entry in graph.MapValue.EntriesValue),
           "configuration no longer owns the linked resolved map")
    owner = fields["fa48"]
    item, = owner.FieldsValue["items"]
    view = item["o"]
    matrix = tuple(view.FieldsValue["f368"]["f08"][f"m{index}"] for index in range(9))
    demand(owner.FieldsValue["n"] == 1 and view.ClassValue == ANNOTATION_CLASS
           and view.FieldsValue["f358"] == "*Top" and view.FieldsValue["f360"] == fields["feb0"] == 200
           and fields["feb4"] == 199 and retained[view.IndexValue] is view
           and pack("<9d", *matrix) == pack("<9d", *annotation_matrix(top).values()),
           "typed Top annotation differs")
    definition = ReadModelDef(archive.Require(DEFINITION), VERSION).GraphValue.DocumentValue.FieldsValue
    display_words = [definition["fad8_0"], definition["fad8_1"]]
    demand(display_words == [1 << 17 if flag else 0, 0], "typed construction-plane setting differs")
    tables = []
    for field in ("f9b8", "f9c0"):
        rows = {item["o"].ClassValue.NameValue: item["o"].FieldsValue
                for item in fields[field].FieldsValue["items"]}
        tables.append([rows["moLengthUserUnits_c"]["fb0"], rows["moUnitSysUnits_c"]["fb0"]])
    demand(tables == [[0, 4], [2, 1]], "typed unit tables differ")

    nodes = IndexFeatures(link)
    boss, = (ReadExtrude(link, node, nodes) for node in nodes.values() if node.ClassValue.NameValue == "moExtrusion_c")
    ring = ReadLineLoop(boss.ProfileValue.FieldsValue["pd_f80"], link)
    starts = tuple(ring.LinesValue[index].StartValue for index in ring.OrderValue)
    ends = tuple(ring.LinesValue[index].EndValue for index in ring.OrderValue)
    coordinates = tuple(tuple(ring.PointsValue[index].FieldsValue["pos"][axis].hex() for axis in ("x", "y"))
                        for index in starts)
    depth = boss.DepthValue.Parameter.FieldsValue["f58"]
    demand(starts[1:] + starts[:1] == ends and coordinates == tuple(point_words(edge.start) for edge in lines(document.sketches[0]))
           and depth.hex() == candidate.PlanValue.DepthValue.hex(), "typed sketch or linked D1 differs")
    body, = mm.bodies
    prism = ReadPrismBody(link, nodes, AllowFirstScope=True, AllowPolygon=True)
    geometry = BuildPrismGeom(prism, body.id, CreatorValue=boss.NodeValue)
    solid, topology = geometry.BrepValue, geometry.TopologyValue
    demand(topology.solid_count == 1, "linked boss did not derive one solid")
    return {"coordinates_m": coordinates, "depth_m": depth.hex(), "map": [graph.MapValue.CounterValue, resolved.MapBase,
             resolved.MapValue.CounterValue], "top": {"id": 200, "slot": view.IndexValue, "frame": [n.hex() for n in matrix]},
            "plane_words": display_words, "unit_table_codes": tables,
            "derived_prism": {"topology": [len(solid.faces), len(solid.edges), len(solid.vertices)],
                              "volume_mm3": topology.volume, "source": "linked native profile, support and boss"}}


def reader_outcomes(base, final, definition):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
    from convert.adapters.solidworks.Archive.Definition.ReadOrdinaryDef import ReadOrdinaryDef

    try:
        ReadOrdinaryDef(definition, VERSION)
        ordinary = {"returned": True}
    except BodyUnsupported as exc:
        ordinary = {"returned": False, "reason": str(exc)}
    public = {}
    final_model = None
    for name, raw in (("base", base), ("final", final)):
        cases = {}
        for mode, flags in (("default", {}), ("without_brep", {"include_brep": False})):
            try:
                document = open_document(raw, source_format="solidworks.sldprt", strict=True, **flags)
                if name == "final" and mode == "without_brep":
                    final_model = document
                driver, = document.parameters
                boss, = (item for item in document.feature_timeline if item.id == driver.owner_id)
                cases[mode] = {"returned": True, "bodies": len(document.bodies),
                               "boss_operation": str(boss.operation),
                               "diagnostics": sorted({entry.code for entry in document.diagnostics})}
            except (ValueError, TypeError) as exc:
                cases[mode] = {"returned": False, "reason": str(exc)}
        public[name] = cases
    demand(final_model is not None, "final archive did not return its model-only document")
    return {"ordinary_definition": ordinary, "public_121": public}, final_model


def main():
    parser = ArgumentParser(description="Generate a fresh part with two explicitly scoped empty owners")
    for name in ("dependency-root", "property-root", "part-request", "appearance-request", "property-request", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--locator", required=True)
    parser.add_argument("--epoch", required=True, type=int)
    args = parser.parse_args()
    props = initialize(args.dependency_root, args.property_root)
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    inputs = ((args.part_request, DOCUMENT_LIMIT), (args.appearance_request, REQUEST_LIMIT),
              (args.property_request, REQUEST_LIMIT))
    part_raw, appearance_raw, prop_raw = (read_bounded(path, limit) for path, limit in inputs)
    document, top, flag = part_request(part_raw)
    appearance, present = read_owner(appearance_raw), props.read_request(prop_raw)
    candidate, mm, raw, streams, property_state = compose(document, top, flag, args.locator, args.epoch, appearance, present, props)
    archive = SldprtArchive.from_bytes(raw, "<fresh part with empty owners>")
    demand(set(archive.streams) == set(streams) and all(archive.Require(name) == data for name, data in streams.items())
           and not any(name.startswith("Kit/") or name.endswith("-Partition") for name in streams), "part stream roster differs")
    link = ReadNativeLink(archive, 0)
    geometry = read_geometry(candidate, document, mm, top, flag, archive, link)
    appearance_read = inspect_generated(archive.Require(DEFINITION), appearance)
    props.check_xml({name: archive.Require(name) for name in props.XML_FILES})
    property_read = props.inspect(archive.Require(PROPERTIES), present)
    demand(property_state == property_read, "typed property owner differs on container readback")
    readers, final_model = reader_outcomes(candidate.BytesValue, raw, archive.Require(DEFINITION))
    owner = read_configuration(mm, final_model, top, archive, link)
    check_dependencies(args.dependency_root.resolve(), args.property_root.resolve())
    check_imports(args.dependency_root.resolve(), args.property_root.resolve())
    demand(tuple(read_bounded(path, limit) for path, limit in inputs) == (part_raw, appearance_raw, prop_raw),
           "a composition request changed")
    args.output.mkdir()
    artifact = write_artifact(args.output, PureWindowsPath(args.locator).name, raw)
    report = {"scope": "generated part; scoped owner and linked CAD wire checks",
              "sdk_revision": REVISION, "property_revision": PROPERTY_REVISION,
              "native_locator": args.locator, "written_at": args.epoch,
              "requests_sha256": {name: digest(request) for name, request in
                                  (("part", part_raw), ("appearance", appearance_raw), ("property", prop_raw))},
              "base_sha256": digest(candidate.BytesValue), "archive": artifact, "configuration": owner, "geometry": geometry,
              "appearance": appearance_read, "property": property_read, "readers": readers,
              "external_generation_attempts": 0, "native_launches": 0,
              "changed_base_streams": sorted(name for name, data in candidate.StreamsValue.items() if streams[name] != data),
              "added_streams": sorted(streams.keys() - candidate.StreamsValue.keys()),
              "clear_streams": {name: [len(data), digest(data)] for name, data in streams.items()}}
    write_artifact(args.output, "Evidence.json", canonical_json(report))
    sys.stdout.buffer.write(canonical_json(report))


if __name__ == "__main__":
    main()
