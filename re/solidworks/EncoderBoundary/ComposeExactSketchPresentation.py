from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from math import isclose
from pathlib import Path, PureWindowsPath
from struct import pack
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "src"), str(ROOT / "re/automation"),
    str(ROOT / "re/solidworks/WriterResearch"), str(Path(__file__).resolve().parent),
]

from ComposeTopAnnotation import REQUEST_SCHEMA as TOP_SCHEMA
from ComposeTopAnnotation import add_top_annotation, annotation_matrix, read_request as read_top_request
from EncoderRoundTrip.Artifacts import canonical_json, digest, read_record, write_artifact
from ExactSketchIntent import demand, lines, make_mm_view, point_words, validate_si_plan
from ExtractTopAnnotation import checked_view
from convert import open_document
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import ReadLineLoop
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


SCHEMA = "kit.research.exact-sketch-presentation.v1"
PLANE_VISIBILITY_BIT = 17


def read_request(payload):
    value = read_record(payload)
    demand(set(value) == {"schema", "document", "display_units", "annotation_view", "show_construction_planes"}
           and value["schema"] == SCHEMA, "expected one exact sketch presentation request")
    demand(value["display_units"] == "mm", "explicit mm display intent is required")
    flag = value["show_construction_planes"]
    demand(type(flag) is bool, "construction-plane visibility must be a JSON boolean")
    demand(canonical_json(value) == payload, "exact sketch presentation request must use canonical JSON")
    document, top = read_top_request(canonical_json({
        "schema": TOP_SCHEMA, "document": value["document"], "annotation_view": value["annotation_view"],
    }))
    return document, top, flag


def construct(document, top, flag, locator, epoch):
    plan = validate_si_plan(document)
    configuration, = document.configurations
    demand(configuration.active is True and configuration.id == top.configuration_id,
           "Top annotation must bind the active neutral configuration")
    mm = make_mm_view(document)
    PlanPartWrite(mm)
    output = RequirePartPath(locator, epoch)
    recipe = MakePartRecipe(plan, epoch)
    demand(not recipe.DefinitionValue.DisplayBits, "plane intent requires the ordinary generated Definition")
    definition = replace(recipe.DefinitionValue, DisplayBits=(PLANE_VISIBILITY_BIT,) if flag else ())
    inputs = BindPartIntent(mm, plan, replace(recipe, DefinitionValue=definition), output)
    CheckPartInput(mm, inputs, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(inputs, plan, allocator)
    add_top_annotation(system.RootValue, top)
    profile = MakePartProfMut(system, inputs, plan, allocator)
    return FinishBlindMut(system, profile, inputs, plan, allocator), mm


def guarded_construct(document, top, flag, locator, epoch):
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    active, attempts = True, []

    def audit(event, _):
        if active and (
            event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.startfile",
                      "os.spawn", "os.posix_spawn", "os.fork", "os.forkpty")
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            attempts.append(event)
            raise RuntimeError(f"external access during combined construction: {event}")

    sys.addaudithook(audit)
    try:
        result = construct(document, top, flag, locator, epoch)
    finally:
        active = False
    demand(not attempts and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "combined construction crossed its offline boundary")
    return result


def inspect_fields(candidate, document, top, flag, archive, link):
    graph, resolved = link.ConfigValue, link.ResolvedValue
    fields = graph.RootValue.FieldsValue
    view = checked_view(graph, archive.Require(link.ConfigName))
    matrix = tuple(view.FieldsValue["f368"]["f08"][f"m{index}"] for index in range(9))
    demand(pack("<9d", *matrix) == pack("<9d", *annotation_matrix(top).values()),
           "typed saved Top matrix differs from the intended signed frame")
    retained = {entry.IndexValue: entry.EntryValue for entry in resolved.MapValue.EntriesValue}
    demand(resolved.MapBase == graph.MapValue.CounterValue == candidate.ConfigValue.MapValue.CounterValue
           and resolved.MapValue.CounterValue == candidate.ResolvedValue.MapValue.CounterValue
           and len(resolved.RootsValue) == len(candidate.ResolvedValue.RootsValue)
           and all(retained.get(entry.IndexValue) is entry.EntryValue for entry in graph.MapValue.EntriesValue),
           "resolved graph does not retain the actual typed configuration map")

    tables = []
    for field in ("f9b8", "f9c0"):
        rows = {row["o"].ClassValue.NameValue: row["o"].FieldsValue for row in fields[field].FieldsValue["items"]}
        tables.append([rows["moLengthUserUnits_c"]["fb0"], rows["moUnitSysUnits_c"]["fb0"]])
    demand(tables == [[0, 4], [2, 1]], "typed display MMGS or analysis MKS table differs")
    definition = ReadModelDef(archive.Require("Contents/Definition"), graph.VersionValue).GraphValue.DocumentValue.FieldsValue
    words = [definition["fad8_0"], definition["fad8_1"]]
    demand(words == [(1 << PLANE_VISIBILITY_BIT) if flag else 0, 0], "typed plane visibility mask differs")

    nodes = IndexFeatures(link)
    owner, = (ReadExtrude(link, node, nodes) for node in nodes.values() if node.ClassValue.NameValue == "moExtrusion_c")
    ring = ReadLineLoop(owner.ProfileValue.FieldsValue["pd_f80"], link)
    starts = tuple(ring.LinesValue[index].StartValue for index in ring.OrderValue)
    ends = tuple(ring.LinesValue[index].EndValue for index in ring.OrderValue)
    points = tuple(tuple(ring.PointsValue[index].FieldsValue["pos"][axis].hex() for axis in ("x", "y")) for index in starts)
    demand(starts[1:] + starts[:1] == ends and points == tuple(point_words(edge.start) for edge in lines(document.sketches[0])),
           "typed native coordinates or endpoint aliases differ")
    native_depth = owner.DepthValue.Parameter.FieldsValue["f58"]
    demand(native_depth.hex() == candidate.PlanValue.DepthValue.hex(), "typed saved D1 differs")
    return {
        "coordinate_words_m": points, "native_unit_table_codes": tables, "definition_display_words": words,
        "show_construction_planes": flag, "d1_m_word": native_depth.hex(),
        "top": {"name": view.FieldsValue["f358"], "id": view.FieldsValue["f360"], "slot": view.IndexValue,
                "configuration_id": top.configuration_id, "matrix_binary64": [value.hex() for value in matrix]},
        "config_next_slot": graph.MapValue.CounterValue, "resolved_base": resolved.MapBase,
        "resolved_next_slot": resolved.MapValue.CounterValue, "resolved_roots": len(resolved.RootsValue),
    }


def inspect_solid(raw, mm, depth):
    decoded = open_document(raw, source_format="solidworks.sldprt", strict=True)
    driver, = decoded.parameters
    boss, = (feature for feature in decoded.feature_timeline if feature.id == driver.owner_id)
    body, = decoded.bodies
    demand(decoded.brep is not None and driver.name == "D1" and driver.role == "driving"
           and driver.attributes["native_value"].hex() == depth.hex()
           and boss.definition.length == driver.value and boss.parameter_ids == (driver.id,)
           and body.final_feature_id == boss.id, "strict SDK readback lost the linked blind extrusion")
    expected, volume, _, bounds = BuildPrism(body.id, mm.support_planes[0].transform, lines(mm.sketches[0]), 0.0, depth / 0.001)
    actual_rings, expected_rings = ReadMassRings(decoded.brep), ReadMassRings(expected)
    matched = [tuple(i for i, wanted in enumerate(expected_rings) if len(actual) == len(wanted)
                     and any(actual == wanted[j:] + wanted[:j] for j in range(len(wanted)))) for actual in actual_rings]
    count = [len(decoded.brep.faces), len(decoded.brep.edges), len(decoded.brep.vertices)]
    demand(body.topology.solid_count == 1 and body.topology.bounding_box == bounds
           and isclose(body.topology.volume, volume, rel_tol=0.0, abs_tol=1e-7)
           and len(actual_rings) == len(expected_rings) and all(len(row) == 1 for row in matched)
           and len(set(matched)) == len(expected_rings)
           and count == [len(expected.faces), len(expected.edges), len(expected.vertices)],
           "strict SDK solid geometry or topology differs")
    return {"topology": count, "volume_mm3": body.topology.volume, "directed_face_rings": len(actual_rings)}


def generate(args):
    payload = args.request.read_bytes()
    document, top, flag = read_request(payload)
    candidate, mm = guarded_construct(document, top, flag, args.locator, args.epoch)
    raw = candidate.BytesValue
    archive = SldprtArchive.from_bytes(raw, "<generated exact sketch presentation>")
    demand(not any(name.startswith("Kit/") or name.endswith("-Partition") for name in archive.streams),
           "combined candidate contains an opaque carrier")
    link = ReadNativeLink(archive, 0)
    fields = inspect_fields(candidate, document, top, flag, archive, link)
    solid = inspect_solid(raw, mm, candidate.PlanValue.DepthValue)
    demand(args.request.read_bytes() == payload, "combined generation changed the persisted request")
    args.output.mkdir()
    retained = write_artifact(args.output, PureWindowsPath(args.locator).name, raw)
    evidence = {"schema": SCHEMA, "request_sha256": digest(payload), "archive": retained,
                "native_locator": args.locator, "written_at": args.epoch,
                "external_generation_attempts": 0, "native_launches": 0,
                "fields": fields, "strict_readback": solid}
    write_artifact(args.output, "Evidence.json", canonical_json(evidence))
    return evidence


if __name__ == "__main__":
    parser = ArgumentParser(description="Compose exact SI sketch, default Top annotation and global plane visibility")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--locator", required=True)
    parser.add_argument("--epoch", type=int, required=True)
    args = parser.parse_args()
    sys.stdout.buffer.write(canonical_json(generate(args)))
