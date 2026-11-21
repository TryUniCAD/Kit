from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from subprocess import run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"


def model_process():
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)

    from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
    from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
    from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
    from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
    from interchange.serialization.Deserialize import FromData
    from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import MakePolygonCase
    from MakePatternAnnotationCatalog import add_catalog_mut, annotation_frame, display_membership

    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    intent = json.load(sys.stdin)
    audit.BeginBuild()
    require(type(intent) is dict and set(intent) == {"views", "active", "shown", "angle_view", "owner"},
            "annotation experiment requires an independently authored neutral request")
    name = intent["owner"]
    plate = FromData(MakePolygonCase(name, ((0.0, 0.0), (79.125, 0.0), (79.125, 48.625), (0.0, 48.625)), False)["document"])
    plan = ProjectPlain(plate)
    settings = replace(MakePartRecipe(plan, 1795092001), OutputValue=SelfFileInput(
        f"C:\\KitPatternAnnotationCatalog\\{name}.SLDPRT", 1795092001))
    def new_model():
        allocator = PersistentIds()
        system = MakePartBaseMut(settings, plan, allocator)
        return system.RootValue, MakePartHeaders(system, settings, allocator)[0]

    def slots(snapshot):
        result = []
        for row in snapshot.EntriesValue:
            value = row.EntryValue
            result.append((row.IndexValue, value.ClassValue if isinstance(value, ArchiveNode) else value))
        return tuple(result)

    model, header = new_model()
    ordinary, ordinary_graph = WriteConfigMut(model, 19000, header)
    version = settings.TargetValue.FileVersion
    add_catalog_mut(model, intent["views"], intent["active"], intent["shown"], version=version)
    members = display_membership(model, intent["angle_view"])
    emitted, written = WriteConfigMut(model, 19000, header)
    decoded = ReadConfigMut(emitted, 19000, header)
    regenerated, replay = WriteConfigMut(decoded.RootValue, 19000, header)
    require(emitted == regenerated and decoded.MapValue == replay.MapValue
            and written.MapValue.CounterValue == decoded.MapValue.CounterValue and slots(written.MapValue) == slots(decoded.MapValue),
            "annotation catalog changed bytes or linked aliases")
    before = ReadConfigMut(ordinary, 19000, header).RootValue.FieldsValue
    after = decoded.RootValue.FieldsValue
    cameras_before = [(view["o"].FieldsValue["f358"], view["o"].FieldsValue["f360"], view["o"].FieldsValue["f368"])
                      for view in before["f9f8"]]
    cameras_after = [(view["o"].FieldsValue["f358"], view["o"].FieldsValue["f360"], view["o"].FieldsValue["f368"])
                     for view in after["f9f8"]]
    rows = [row["o"].FieldsValue for row in after["fa48"].FieldsValue["items"]]
    require(cameras_before == cameras_after and [row["f358"] for row in rows] == [row["name"] for row in intent["views"]]
            and after["fa48"].FieldsValue["n"] == len(rows) and len({row["f360"] for row in rows}) == len(rows)
            and all(row["f368"] == annotation_frame(choice["basis"]) and row["f3e8#0"] is row["f3e8"] is None
                    for row, choice in zip(rows, intent["views"], strict=True))
            and display_membership(decoded.RootValue, intent["angle_view"]) == members
            and any(row[0] == intent["angle_view"] and row[1] != members["f2b0"][0]["v"] for row in cameras_after),
            "generated membership lost the actual view transform or collided with a same-name camera")
    normalized = ReadConfigMut(emitted, 19000, header).RootValue
    normalized.FieldsValue["fa48"].FieldsValue.update(before["fa48"].FieldsValue)
    for field in ("feb0", "feb4", "nec8", "fec0"):
        normalized.FieldsValue[field] = before[field]
    require(WriteConfigMut(normalized, 19000, header)[0] == ordinary,
            "annotation registration changed an owner outside the catalog and its explicit state")
    rejected = {}
    for name, changed in (("duplicate_names", {"views": [intent["views"][0]] * 2}),
                          ("unknown_active", {"active": "Missing"}), ("unknown_shown", {"shown": ["Missing"]}),
                          ("duplicate_shown", {"shown": [None, None]}),
                          ("invalid_orientation", {"views": [{**intent["views"][0], "basis": [[1.0, 0.0, 0.0]] * 3}]})):
        mutated = {**intent, **changed}
        fresh, fresh_header = new_model()
        try:
            add_catalog_mut(fresh, mutated["views"], mutated["active"], mutated["shown"], version=version)
        except ValueError as error:
            rejected[name] = str(error)
            require(WriteConfigMut(fresh, 19000, fresh_header)[0] == ordinary, "invalid intent changed the ordinary base")
    require(len(rejected) == 5 and not audit.DeniedReads, "one neutral annotation guard failed")
    result = {"request_sha256": digest(encode(intent)), "config_sha256": digest(emitted), "config_bytes": len(emitted),
              "ordinary_config_sha256": digest(ordinary), "ordinary_config_bytes": len(ordinary),
              "config_map_delta": written.MapValue.CounterValue - ordinary_graph.MapValue.CounterValue,
              "only_catalog_and_explicit_state_changed": True,
              "annotation_ids": {row["f358"]: row["f360"] for row in rows}, "fEB0": after["feb0"],
              "active": after["feb4"], "shown": [row["v"] for row in after["fec0"]],
              "actual_join_to_angle_view": members["f2b0"][0]["v"], "refusals": rejected,
              "guarded_runtime_reads": len(audit.DeniedReads), "cad_files_written": 0}
    sys.stdout.buffer.write(encode(result))


def static_proof(path):
    from ProvePatternPlaneDirectionRule import Image, MODULES, module

    image = Image(path / "sldmodu.dll")
    recorded = module(image, MODULES[image.path.name])
    ranges = {
        "ownerless_annotation_init": (0x4C7E8470, 0x4C7E8763, "a65bf1233bd1eafc72584ff7c0609bda37d2cd083590c3acc0f3dd7ad87ca564"),
        "actual_shown_id_add": (0x4C037010, 0x4C03707E, "e2d418b76f0ca40b0c6615f13db7be0bb106c30dbe2bd636582633b9134a8c71"),
        "current_view_id_getter": (0x4C01EFD0, 0x4C01EFD7, "77a1116e9d7c39056d3d2b5af28928b0b04526fb3789e42352801ee048300781"),
        "increment_frontier_for_view": (0x4C013C86, 0x4C013C97, "76972655acf61f59fdca317fb79daf9a6e927d707894ed9ba2e2c0aaf28167b3"),
        "increment_frontier_for_parent": (0x4C7E9A72, 0x4C7E9A82, "d0e08eef571bcefdda94ca25743506a7b9818d97d2649d3cfbb7a74c1282d228"),
        "write_high_active_and_shown": (0x4C234B93, 0x4C234C01, "e3c3ce1a3ec952fbcbbab6a3f851f62e4eb78e1e80e417d0f61992ce97ffecfd"),
    }
    for role, (start, end, expected) in ranges.items():
        actual = digest(image.bytes(start, end))
        require(expected == actual, "build-bound annotation model boundary changed")
        recorded[role] = {"address_range": [hex(start), hex(end)], "sha256": actual}
    return recorded


def disclosed(share, views):
    from CheckPatternAngleOwners import annotation_catalog
    from MakePatternAnnotationCatalog import annotation_node
    from PatternAngleWire import ANGLE_PLANE
    from ProvePatternAngleOwners import document_rows, exact_config

    examples = {}
    for path, pin, row in document_rows(share):
        if row["plane_data_class"] != ANGLE_PLANE and path.name not in ("D01X.SLDPRT", "D02Y.SLDPRT"):
            continue
        _, _, cfg, _ = exact_config(path, pin)
        model = cfg.RootValue
        catalog = annotation_catalog(model)
        frontier = model.FieldsValue["feb0"]
        active = model.FieldsValue["feb4"]
        ids = [node["f360"] for node in catalog]
        require(ids == list(range(200, frontier + 1)) and active == 199
                and model.FieldsValue["fec0"] == [{"v": 199}], "checked annotation order or default activity changed")
        for row in catalog:
            name = row["f358"]
            expected = annotation_node(name, views[name], row["f360"]).FieldsValue
            require(all(expected[field] == row[field] for field in ("f368", "f370", "f3d8", "f3d0", "f3f0", "f3e0", "f3e8",
                        "f3f4", "f3f8", "f2f0", "f3fc", "f408", "f400", "f404")) and row["f3e8#0"] is None,
                    "checked source view lost its predicted frame or annotation class members")
        examples[path.name] = {"sha256": pin, "named_source_ids": [[node["f358"], node["f360"]] for node in catalog],
                               "active": active, "shown": [199]}
    require(len(examples) == 6, "expected six explicitly disclosed independent catalog cases")
    return examples


def main():
    if sys.argv[1:] == ["--model-only"]:
        model_process()
        return
    parser = ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    x, y, z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    neg_x, neg_z = (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)
    bases = {"*Top": (x, neg_z, y), "*Back": (neg_x, y, neg_z), "*Front": (x, y, z),
             "*Left": (z, y, neg_x)}
    cases = (
        {"owner": "FirstAnnotationOrder", "views": ["*Back", "*Top"], "active": None, "shown": [None], "angle_view": "*Back"},
        {"owner": "SecondAnnotationOrder", "views": ["*Top", "*Front", "*Back"], "active": "*Top", "shown": ["*Back", None], "angle_view": "*Back"},
    )
    runs = []
    for case in cases:
        plan = {**case, "views": [{"name": name, "basis": bases[name]} for name in case["views"]]}
        argv = (sys.executable, "-I", "-B", str(HERE), "--model-only")
        first, second = (run(argv, cwd=ROOT, input=encode(plan), capture_output=True, check=True, timeout=20) for _ in range(2))
        require(not first.stderr and not second.stderr and first.stdout == second.stdout, "guarded annotation model is not deterministic")
        runs.append(json.loads(first.stdout))
    require(runs[0]["actual_join_to_angle_view"] != runs[1]["actual_join_to_angle_view"]
            and runs[0]["config_bytes"] != runs[1]["config_bytes"] and runs[0]["active"] != runs[1]["active"],
            "expected independent catalog order, count and activity contrasts")
    report = {"schema": "kit.sw2026.research-only.annotation-catalog.v1", "guarded_neutral_models": runs,
              "static_ownership": static_proof(args.binaries), "disclosed_catalogs": disclosed(args.disclosed_share, bases),
              "neutral_processes": 4, "cad_files_written": 0, "native_or_heldout_calls": 0,
              "tools": {name: digest(HERE.with_name(name).read_bytes()) for name in (HERE.name, "MakePatternAnnotationCatalog.py")}}
    with args.output.open("xb") as file:
        file.write(encode(report))
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
