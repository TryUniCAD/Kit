from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
from subprocess import run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1] / "serial")]

from Classes import registry
from CorrelateMaterialTree import (
    IO_EVENTS, STREAM, SWATCH, checked, digest, encode, load_inputs, require, swatch_span, xml_model,
)
from defs.Visual import load_visual_states, store_visual_states
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrText import ReadCmgrText
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyMgrs import ReadEmptyMgrs
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import KSourceBytesKey, SldprtAdapter
from convert.adapters.solidworks.Core.TypedResolved.Materials.BindNamedMat import BindNamedMat
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadNamedMat import ReadNamedMat
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.materials.MaterialRecord import MaterialRecord


BASE = "d3a1134c18027fa8a75676cf3cc7a8b9418395b3"
SDK_TREE = "30dab695fbd7704c3ac227e925a77baf81deec83"
OLDER = "48d1a287e6137ac69f1156aa6cbba8fca590e114dbc3a9c33e16ac5ed2d9f1d7"
MEASUREMENTS = "re/solidworks/measurements/2026/"
VISUAL = "ThirdPtyStore/VisualStates"
PACKAGE_LAYOUT = "src/convert/adapters/solidworks/Config/RootLayout.json"
PACKAGE_LAYOUT_SHA = "be92c068506d33c254efe371277b6c003ab103959d1560f1568f9028a6290a29"


def read_named(archive):
    graphs = []

    def observe(frame, event, _):
        if event == "call" and frame.f_code is BindNamedMat.__code__:
            graphs.append((frame.f_locals["PartGraph"], frame.f_locals["ManagerValue"]))

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        result = ReadNamedMat(archive)
    finally:
        sys.setprofile(previous)
    require(len(graphs) == 1, "named material did not bind its two physical archive graphs")
    part, manager = graphs[0]
    active = manager.RootValue.FieldsValue["f368"]
    atom = part.RootValue.FieldsValue["fd88"]["atoms"][0]["o"]
    return result, part.RootValue, active, atom


def checked_node(value, name, reader):
    node = RequireNative(value, name)
    require(any(entry.IndexValue == node.IndexValue and entry.EntryValue is node
                for entry in reader.map_state().state.EntriesValue),
            "display owner is detached from its actual archive map")
    return node


def read_holder(archive, reg, active):
    data = archive.Require(VISUAL)
    with reg.track_usage("load", VISUAL, sources=archive.Streams) as loading:
        document, reader = load_visual_states(data, reg)
    with reg.track_usage("store", VISUAL) as storing:
        replay = store_visual_states(document, reg)
    require(replay == data and not document.tail and not reader.left()
            and all(row.completed for row in (loading, storing))
            and all(not row.snapshot()[name] for row in (loading, storing)
                    for name in ("raw_operations", "missing_schemas", "provisional_schemas")),
            "display store lacks an exact typed replay")
    state = checked_node(document.head["root"], "visStateKeyData_c", reader).FieldsValue
    selected, = state["f0f0"]
    state_id = selected["id"]
    require(document.head["file_version"] == 19000 and document.head["shown"] == 0
            and state["n_comps"] == 0 and state["n_ents"] == len(state["f78"]) == 6
            and state["f118"] == [{"key": active.FieldsValue["f08"], "value": state_id, "one": 1}],
            "display state does not own the selected actual configuration")
    holder, = (row for row in state["f78"] if row["ref"].ClassValue.NameValue == "moCompHolder_c")
    reference = checked_node(holder["ref"], "moCompHolder_c", reader)
    unit = checked_node(reference.FieldsValue["f58"], "moUnitComponent_c", reader)
    attrs, = holder["attrs"]
    visual, visibility = (row["o"] for row in attrs["objs"])
    visual = checked_node(visual, "visStateVisualPropertiesAttribute_c", reader)
    visibility = checked_node(visibility, "visStateVisualStateAttribute_c", reader)
    require(unit.FieldsValue == {"owner": None, "has_ext": 0}
            and holder["m"] == 1 and attrs["k"] == 2
            and attrs["key"] == visual.FieldsValue["f08"] == visibility.FieldsValue["f08"] == state_id,
            "display attribute is not attached to the actual part self or selected state")
    result = checked_node(visual.FieldsValue["f10"], "moVisualProperties_c", reader)
    return result, {"sha256": digest(data), "bytes": len(data), "map_counter": reader.count,
                    "configuration_id": active.FieldsValue["f08"], "state_id": state_id,
                    "state_name": selected["name"], "holder_slot": reference.IndexValue, "exact_replay": True}


def changes(first, second, prefix=""):
    if isinstance(first, dict) and isinstance(second, dict):
        for key in sorted(first.keys() | second.keys()):
            path = prefix + key
            if key not in first or key not in second:
                yield path
            else:
                yield from changes(first[key], second[key], path + ".")
    elif first != second:
        yield prefix[:-1]


def rgb(word):
    require(type(word) is int and 0 <= word <= 0xFFFFFF, "visual uses a nonordinary color word")
    return [(word >> shift) & 255 for shift in (0, 8, 16)]


def summarize(visual, identity):
    fields = visual.FieldsValue
    material = fields["f20"]
    classic, pbr = material["f90"], fields["f88"]
    texture = material.get("f80")
    require(ReadCmgrText(material["f20"]) == identity
            and (material["has90"], material["has98"], fields["has88"]) == (1, 0, 1)
            and material["has80"] == int(texture is not None)
            and (texture is None or len(texture) == 19), "visual material does not match its physical assignment")
    return {
        "slot": visual.IndexValue, "span": [visual.StartOffset, visual.EndOffset],
        "model_rgb": rgb(fields["f0c"]), "classic_rgb": rgb(classic["f14"]),
        "legacy_transparency_f58": material["f58"], "classic_roughness_f74": classic["f74"],
        "pbr_albedo_f10": [pbr[f"f10_{index}"] for index in range(3)],
        "pbr_roughness_f2c": pbr["f2c"], "pbr_metallic_f28": pbr["f28"],
        "pbr_field_count": len(pbr), "render_id_words": [classic["f00"], classic["f04"]],
        "classic_locator_sha256": digest(encode(classic["f68"])),
        "texture": None if texture is None else {
            "field_count": len(texture), "typed_sha256": digest(encode(texture)),
            "f70_text_length": len(ReadCmgrText(texture["f70"])),
        },
    }


def public_result(raw):
    document = SldprtAdapter().read(BytesIO(raw), ReadOptions(strict=True))
    typed = document.metadata["solidworks.typed_resolved_semantics"]
    return {
        "bodies": len(document.bodies), "material_records": len(document.materials),
        "material_links": [body.material_id is not None for body in document.bodies],
        "material_capability": any(value.value == "materials" for value in document.capabilities),
        "typed_status": typed["status"], "typed_diagnostic": typed["diagnostic"],
        "writer_qualified": typed["public_writer_qualified"],
        "source_retained_as_bytes": document.metadata.get(KSourceBytesKey) == raw,
    }


def worker():
    raw = sys.stdin.buffer.read()
    reg = registry()
    for module in (
        "Behavior.DocumentIo", "Models.DocumentProvenance", "Models.DocumentWalk",
        "Validation.DocumentAssemblyValidate", "Validation.DocumentFeatureValidate",
        "Validation.DocumentReferenceValidate",
    ):
        import_module("interchange.document." + module)
    for name in ("ascii", "latin-1", "cp1252", "utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        lookup(name)
    blocked = []
    layout_reads = []
    reading_public = False
    layout_path = str(ROOT / PACKAGE_LAYOUT)
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND

    def guard(event, args):
        if event == "open" and reading_public and args[0] == layout_path and not args[2] & write_flags:
            layout_reads.append(args[0])
            return
        if event in IO_EVENTS or event.startswith(("socket.", "subprocess.")):
            blocked.append(event)
            raise RuntimeError("assigned appearance inspection attempted runtime input: " + event)

    sys.addaudithook(guard)
    archive = SldprtArchive.FromBytes(raw)
    named, part, active, atom = read_named(archive)
    identity = f"{named.CatalogValue}|{named.MaterialName}|{named.NativeId}"
    part_visual = RequireNative(part.FieldsValue["f78"], "moVisualProperties_c")
    cfg_visual = RequireNative(active.FieldsValue["f78"], "moVisualProperties_c")
    holder, display = read_holder(archive, reg, active)
    require(len({part_visual, cfg_visual, holder}) == 3
            and part_visual.FieldsValue == cfg_visual.FieldsValue,
            "independent physical appearance owners lost their measured values")
    definition = ReadModelDef(archive.Require("Contents/Definition"), 19000).GraphValue
    manager = ReadEmptyMgrs(definition).AppearanceValue
    tree = archive.Require(STREAM)
    elements, offsets = xml_model(tree)
    swatch_span(tree, elements, offsets[SWATCH][0])
    reading_public = True
    try:
        public = public_result(raw)
    finally:
        reading_public = False
    require(not blocked, "reader suppressed an external access refusal")
    return {
        "file_sha256": digest(raw), "physical": asdict(named), "atom_id": atom.FieldsValue["f140"],
        "part": summarize(part_visual, identity), "configuration_visual_slot": cfg_visual.IndexValue,
        "holder": summarize(holder, identity), "holder_changed_fields": list(changes(
            part_visual.FieldsValue, holder.FieldsValue)),
        "display": display, "definition_manager": asdict(manager), "tree_sha256": digest(tree),
        "swatch_rgb_sha256": digest(elements[SWATCH].attrib["RGB"].lower().encode("ascii")),
        "public_read": public,
        "ordinary_packaged_layout_reads": len(layout_reads), "runtime_external_accesses": 0,
    }


def check_revision():
    coupled = ("src", "re/tooling/sw2026/serial", "re/tooling/sw2026/materials/CorrelateMaterialTree.py")
    actual = run(("git", "rev-parse", "HEAD:src"), cwd=ROOT, capture_output=True, check=True, text=True)
    untracked = run(("git", "ls-files", "--others", "--exclude-standard", "--", *coupled),
                    cwd=ROOT, capture_output=True, check=True, text=True)
    delta = run(("git", "diff", "--quiet", BASE, "--", *coupled), cwd=ROOT, check=False)
    require(actual.stdout.strip() == SDK_TREE and not untracked.stdout and delta.returncode == 0,
            "inspection requires the pinned SDK source tree and research serializers")


def measure(source):
    check_revision()
    original = json.loads(checked(ROOT, MEASUREMENTS + "SdkAssignedMaterialRead01.json", OLDER))
    _ = checked(ROOT, PACKAGE_LAYOUT, PACKAGE_LAYOUT_SHA)
    result = {}
    for role, (raw, logged) in load_inputs(source).items():
        process = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=raw,
                      capture_output=True, check=False, timeout=50)
        require(process.returncode == 0 and not process.stderr, process.stderr.decode("utf-8"))
        now = json.loads(process.stdout)
        earlier = original["cases"][role]
        physical = now["physical"]
        identity = f"{physical.pop('CatalogValue')}|{physical.pop('MaterialName')}|{physical['NativeId']}"
        require(now["file_sha256"] == logged["file_sha256"]
                and physical == earlier["observation"]
                and identity == logged["owners"]["active_config_material"]
                and now["atom_id"] == earlier["graph"]["solid_atom_id"]
                and now["tree_sha256"] == earlier["material_tree_sha256"],
                "appearance intake changed the exact physical assignment or source")
        now["catalog_identity_sha256"] = digest(identity.encode("utf-8"))
        public = now["public_read"]
        require(public["bodies"] == 1 and public["material_records"] == 0 and public["material_links"] == [False]
                and not public["material_capability"] and not public["writer_qualified"]
                and public["source_retained_as_bytes"] and public["typed_status"] == "unsupported"
                and public["typed_diagnostic"] == earlier["ordinary_read"],
                "the public appearance projection boundary changed")
        require(now["holder_changed_fields"] in ([], ["f20.f90.f00"])
                and now["ordinary_packaged_layout_reads"] == 1,
                "the exact display or ordinary reader boundary changed")
        result[role] = now
    textured = tuple(row["part"]["texture"] for row in result.values() if row["part"]["texture"] is not None)
    require(len(textured) == 4 and all(row["f70_text_length"] == 0 for row in textured)
            and len({row["typed_sha256"] for row in textured}) == 2,
            "the disclosed primary texture contrasts changed")
    first, second = (result[case] for case in ("D01Corner/Author", "D02Center/Swap"))
    require(first["physical"] == second["physical"]
            and first["part"]["model_rgb"] != second["part"]["model_rgb"]
            and first["part"]["pbr_albedo_f10"] != second["part"]["pbr_albedo_f10"]
            and first["swatch_rgb_sha256"] != second["swatch_rgb_sha256"],
            "fixed material fails to discriminate the independent visual values")
    require(first["part"]["model_rgb"] != first["part"]["classic_rgb"],
            "exercised model and classic color no longer differ")
    return {"schema": "kit.sw2026.assigned-appearance-projection.v1", "sdk_revision": BASE,
            "sdk_src_tree": SDK_TREE, "source_method_sha256": digest(HERE.read_bytes()),
            "ordinary_packaged_layout_sha256": PACKAGE_LAYOUT_SHA,
            "prior_physical_receipt_sha256": OLDER, "native_build": "34.5.2.0604",
            "fresh_guarded_processes": len(result), "native_processes": 0, "heldout_credit": 0,
            "portable_material_record_fields": list(MaterialRecord.__dataclass_fields__),
            "cases": result}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(encode(worker()))
    else:
        require(args.source is not None and args.output is not None, "provide the exact disclosed root and new receipt path")
        report = measure(args.source)
        with args.output.open("xb") as output:
            output.write(encode(report))
