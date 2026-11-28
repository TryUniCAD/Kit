from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from itertools import chain
from math import isclose
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
from tempfile import TemporaryDirectory
import json
import os
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
REVISION = "bd835aab5fc01426976b2e2792129d806116dfc9"
SOURCE_TREE = "a207312f5b355adf422edcec68a0fd9f260c5397"
PRIOR = "re/solidworks/measurements/2026/SdkNestedNeutralNative01.json"
PRIOR_SHA = "aa786c6aa4bc7bdae15662c4b4908205b7a0fda7fdb5bb1bb503594a6b0fb967"
AUTHOR = "re/tooling/sw2026/AuditNestedNeutralComposition.py"
EXPECTED_CASES = ("SdkNestedNeutralNative03", "SdkRepeatedNeutralNative03")
IDENTITY = tuple(int(index % 5 == 0) for index in range(16))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, pin, size=None):
    require(not path.is_symlink(), f"unexpected symlink: {path.name}")
    raw = path.read_bytes()
    require(digest(raw) == pin and (size is None or len(raw) == size), f"frozen identity differs: {path.name}")
    return raw


def git(*arguments):
    return check_output(("git", "-C", str(ROOT), *arguments))


def refusal(action, kind, prefix):
    try:
        action()
    except Exception as error:
        require(type(error).__name__ == kind and str(error).startswith(prefix), "a different refusal occurred")
        return {"error": kind, "diagnostic": prefix}
    raise ValueError("unsafe re-export or preparation succeeded")


class FrozenReads:
    def __init__(self, files):
        self.files = frozenset(files)
        self.folder = next(iter(files)).parent
        self.code = (ROOT / "src", ROOT / "re/tooling/sw2026", Path(os.__file__).resolve().parent)
        self.reads = set()
        self.denied = []
        self.active = True

    def inspect(self, event, arguments):
        if not self.active:
            return
        if event == "open":
            name, _, flags = arguments
            if isinstance(name, (str, bytes)) and not flags & (os.O_ACCMODE | os.O_CREAT | os.O_TRUNC):
                path = Path(os.fsdecode(name))
                if path in self.files:
                    self.reads.add(path.name)
                    return
                if path.suffix in (".py", ".pyc") and any(path.is_relative_to(root) for root in self.code):
                    return
            self.denied.append(event)
            raise PermissionError("readback attempted an undeclared data open or write")
        if event in ("os.listdir", "os.scandir"):
            path = Path(os.fsdecode(arguments[0])) if isinstance(arguments[0], (str, bytes)) else None
            if path is not None and (path == self.folder or any(path.is_relative_to(root) for root in self.code)):
                return
            self.denied.append(event)
            raise PermissionError("readback attempted undeclared directory discovery")
        if event.startswith(("socket.", "subprocess.", "ctypes.", "winreg.")) or event in (
            "os.exec", "os.system", "os.startfile", "os.posix_spawn", "os.fork", "os.mkdir",
            "os.rename", "os.remove", "os.rmdir", "os.link", "os.symlink",
        ):
            self.denied.append(event)
            raise PermissionError("readback attempted an external process or mutation")


def difference(left, right):
    return max((abs(x - y) for x, y in zip(left, right, strict=True)), default=0.0)


def multiply(left, right):
    return tuple(sum(left[row * 4 + term] * right[term * 4 + col] for term in range(4))
                 for row in range(4) for col in range(4))


def authored_paths(rows, owner, names=(), pose=IDENTITY):
    for row in rows[owner]:
        key = (owner, row.name)
        world = multiply(pose, row.transform.values)
        outstanding = (*names, key)
        yield outstanding, world
        yield from authored_paths(rows, row.definition_id, outstanding, world)


def scope(document):
    from interchange.Features.FeatureKinds import NativeFeature
    from interchange.document.Models.DocumentProvenance import HasProvenance

    report = document.metadata["solidworks.typed_resolved_semantics"]
    tree = report["native_tree"]
    require(HasProvenance(document) and "solidworks_source_bytes" in document.metadata,
            "forensic read lost retained source evidence")
    require("kit.research_read_status" not in document.metadata and "name" not in document.metadata,
            "default read classification or document title changed")
    return {
        "retained_source_wrapper": True, "document_title": None,
        "source_attributes": sorted(document.source.attributes),
        "diagnostics": [{"code": row.code, "message": row.message} for row in document.diagnostics],
        "native_only_timeline_count": sum(isinstance(row.definition, NativeFeature) for row in document.feature_timeline),
        "typed_feature_count": len(report["feature_identities"]),
        "legacy_only_feature_ids": list(report["legacy_only_feature_ids"]),
        "typed_geometry_projection": report["typed_geometry_projection"],
        "public_full_linked_graph_flag": report["full_linked_graph"],
        "native_tree": {key: tree[key] for key in ("status", "diagnostic", "full_native_tree_qualified")
                        if key in tree},
        "native_tree_rows": len(tree.get("rows", ())),
    }


def leaf_semantics(document, authored):
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import ProjectBlind
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import ReadLineLoop
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import RequireBossDef
    from interchange.Features.FeatureExtrude import ExtrudeFeature

    sketch, = document.sketches
    expected_sketch, = authored.sketches
    boss, = (row for row in document.feature_timeline if isinstance(row.definition, ExtrudeFeature))
    expected_boss, = authored.feature_timeline
    param, = document.parameters
    expected_param, = authored.parameters
    body, = document.bodies
    expected_body, = authored.bodies
    brep, = document.brep.bodies
    want_plane, = [row for row in authored.support_planes if row.id == expected_sketch.support_plane_id]
    plane, = [row for row in document.support_planes if row.id == sketch.support_plane_id]
    require(plane.name == want_plane.name == "Front Plane" and plane.transform == want_plane.transform
            and sketch.name == expected_sketch.name and len(sketch.entities) == 4
            and not (sketch.constraints or expected_sketch.constraints)
            and sketch.closed_profile_entity_ids == (tuple(row.id for row in sketch.entities),),
            "leaf sketch, live support, constraints, or loop changed")
    require(boss.name == expected_boss.name and boss.sketch_id == sketch.id
            and (str(boss.operation), str(expected_boss.operation)) == ("join", "create")
            and boss.definition == expected_boss.definition
            and boss.parameter_ids == (param.id,) and param.owner_id == boss.id
            and (param.name, param.value, param.role, param.expression)
            == (expected_param.name, expected_param.value, expected_param.role, expected_param.expression)
            and body.final_feature_id == boss.id and brep.design_body_id == body.id,
            "leaf boss, editable depth, or neutral B-rep owner changed")
    geometry = tuple((row.geometry.start.x, row.geometry.start.y,
                      row.geometry.end.x, row.geometry.end.y) for row in sketch.entities)
    expected = tuple((row.geometry.start.x, row.geometry.start.y,
                      row.geometry.end.x, row.geometry.end.y) for row in expected_sketch.entities)
    require(tuple((row.kind, row.construction, row.fixed) for row in sketch.entities) ==
            tuple((row.kind, row.construction, row.fixed) for row in expected_sketch.entities),
            "leaf sketch entity type or flags changed")
    line_error = difference(tuple(chain.from_iterable(geometry)), tuple(chain.from_iterable(expected)))
    width = max(row[0] for row in expected) - min(row[0] for row in expected)
    height = max(row[1] for row in expected) - min(row[1] for row in expected)
    depth = expected_param.value.value
    topology = body.topology
    counts = (topology.solid_count, topology.shell_count, topology.face_count, topology.edge_count, topology.vertex_count)
    limits = topology.bounding_box
    bounds = (limits.minimum.x, limits.minimum.y, limits.minimum.z, limits.maximum.x, limits.maximum.y, limits.maximum.z)
    require(line_error <= 1e-12 and counts == (1, 1, 6, 12, 8) and topology.valid
            and isclose(topology.volume, width * height * depth, rel_tol=1e-12)
            and isclose(topology.surface_area, 2 * (width * height + width * depth + height * depth), rel_tol=1e-12)
            and difference(bounds, (-width / 2, -height / 2, 0, width / 2, height / 2, depth)) <= 1e-12,
            "leaf B-rep disagrees with independent authored prism metrics")
    return {
        "profile": sketch.name, "support": plane.name, "lines": len(geometry), "constraints": 0,
        "peak_line_coordinate_delta_mm": line_error, "feature": boss.name, "read_operation": str(boss.operation),
        "authored_operation": str(expected_boss.operation),
        "end_condition": str(boss.definition.end_condition), "driving_parameter": param.name, "depth_mm": depth,
        "body_caption": body.name, "authored_body_caption": expected_body.name, "body_id": body.id,
        "brep_design_body_id": brep.design_body_id, "topology": counts, "volume_mm3": topology.volume,
        "area_mm2": topology.surface_area, "bounds_mm": bounds,
        "guards": {
            "plain_planner": refusal(lambda: PlanPartWrite(document), "ValueError",
                                     "plain part preparation does not admit unresolved or extended source state"),
            "blind_projection": refusal(lambda: ProjectBlind(document, ReadLineLoop), "ValueError",
                                       "plain boss candidate does not admit assemblies drawings or native boundary payloads"),
            "actual_boss_operation": refusal(lambda: RequireBossDef(boss), "ValueError",
                                            "ordinary extrusion requires its actual operation definition"),
        },
    }


def physical_occurrences(link, expected, manifest):
    from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import ReadRigidXform
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode

    owner = link.ConfigValue.RootValue
    physical = owner.FieldsValue["f68"]["list"]
    require(physical["n"] == len(expected), "native owner occurrence count differs")
    rows = []
    for wire, want in zip(physical["items"], expected, strict=True):
        node = RequireNode(wire["o"], "moReference_c")
        fields = node.FieldsValue
        cfg = fields["f3c0"]
        child = manifest[want.definition_id]
        key = ReadFileKey(RequireNode(fields["f3b0"], "moExtObject_c"))
        matrix, origin = ReadRigidXform(fields["f360"])
        pose = tuple(component for axis in range(3) for component in
                     (matrix[axis], matrix[axis + 3], matrix[axis + 6], 1000 * origin[axis])) + (0, 0, 0, 1)
        delta = difference(pose, want.transform.values)
        require(ReadNodeName(node) == want.name and key[1] == child["encoded_path"]
                and (cfg["f10"], cfg["f08"]) == (0, want.configuration_name)
                and delta <= 1e-12, "native occurrence order, selected config, external identity, or pose changed")
        rows.append({"name": want.name, "feature_id": fields["f08"], "target": child["file"],
                     "external_key_sha256": digest(json.dumps(key).encode()),
                     "configuration": [cfg["f10"], cfg["f08"]], "pose_delta": delta})
    return rows


def assembly_semantics(document, link, archive, authored, owner_id, manifest, folder):
    from convert.adapters.solidworks.Assembly.Assembly import ComponentTreeStream, XmlRoot
    from convert.adapters.solidworks.Assembly.Display.ReadDisplayXml import KDisplayNs
    from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmDef import CheckAsmDef
    from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import ReadNestedAsm
    from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedLeaf import ReadNestedLeaf

    graph = document.assembly
    expected = authored.assembly
    want_defs = {row.id: row for row in expected.definitions}
    want_rows = {key: tuple(row for row in expected.instances if row.owner_definition_id == key) for key in want_defs}
    expected_paths = list(authored_paths(want_rows, owner_id))
    expected_ids = {owner_id, *(row.definition_id for path, _ in expected_paths
                                for owner, name in path for row in want_rows[owner] if row.name == name)}
    filenames = {value["file"]: key for key, value in manifest.items()}
    files = {}
    documents = {row.id: row.document for row in graph.documents}
    for row in graph.definitions:
        name = Path(row.source_path).name
        key = filenames[name]
        require(Path(row.source_path) == folder / name and row.kind == want_defs[key].kind
                and row.configuration_name == want_defs[key].configuration_name
                and row.configuration_id == "0"
                and row.attributes["native_source_path"] == manifest[key]["encoded_path"], "definition resolved to an incorrect file or config")
        embedded = documents.get(row.document_id)
        if key == owner_id:
            require(row.id == graph.root_definition_id and embedded is None, "assembly root is not the physical open")
        else:
            require(embedded is not None and Path(embedded.source.path) == folder / name
                    and embedded.source.sha256 == row.source_sha256 == manifest[key]["sha256"],
                    "linked definition cannot identify its actual frozen document")
            current, = embedded.configurations
            require(current.active and current.name == row.configuration_name
                    and str(current.attributes["native_configuration_id"]) == row.configuration_id,
                    "linked document's selected config differs from the raw native id")
            require(row.body_ids == tuple(body.id for body in embedded.bodies), "wrong linked design body IDs")
        label = refusal(lambda: CheckAsmDef(row), "ValueError",
                        "definition has unsupported cached geometry or external source references")
        files[row.id] = {"id": key, "file": name, "caption": row.name, "expected_caption": want_defs[key].name,
                         "configuration_name": row.configuration_name, "raw_config_id": row.configuration_id,
                         "linked_typed_config_id": (embedded or document).configurations[0].id,
                         "bounded": row.bounding_box is not None, "source_sha256": manifest[key]["sha256"],
                         "holds_document": embedded is not None, "body_ids": row.body_ids,
                         "provenance": row.provenance is not None,
                         "definition_guard": label}
        if embedded is not None and embedded.assembly is not None:
            deferred = [item for item in embedded.assembly.definitions if item.id != embedded.assembly.root_definition_id]
            require(not embedded.assembly.documents and len(deferred) == len({value.definition_id for value in want_rows[key]})
                    and all(item.attributes.get("source_resolution") == "deferred" for item in deferred),
                    "embedded subassembly unexpectedly owns a second physical definition graph")
            require([item.name for item in embedded.assembly.instances] == [item.name for item in want_rows[key]],
                    "embedded subassembly occurrence view differs")
            files[row.id]["embedded_assembly_occurrences"] = len(embedded.assembly.instances)
            files[row.id]["embedded_deferred_definitions"] = len(deferred)
        if embedded is not None and str(row.kind) == "part":
            files[row.id]["leaf_guard"] = refusal(lambda: ReadNestedLeaf(row, embedded), "ValueError",
                                                  "configuration has unsupported inherited or extended state")
    require({row["id"] for row in files.values()} == expected_ids and len(files) == len(expected_ids)
            and len(documents) == len(expected_ids) - 1
            and {row.document_id for row in graph.definitions if row.document_id} == set(documents),
            "physical definition inventory differs")

    instances = {}
    orders = {}
    local_error = 0.0
    physical = physical_occurrences(link, want_rows[owner_id], manifest)
    for definition in graph.definitions:
        owner = files[definition.id]["id"]
        actual_rows = sorted((row for row in graph.instances if row.owner_definition_id == definition.id), key=lambda row: row.order)
        require(tuple(int(row.id.rsplit(":", 1)[-1]) for row in actual_rows) == definition.attributes["child_occurrence_ids"],
                "public owner occurrence IDs do not match its index")
        if owner == owner_id:
            require([row.attributes["native_feature_id"] for row in actual_rows] == [row["feature_id"] for row in physical],
                    "index occurrence IDs do not match native feature owners")
        for actual, want in zip(actual_rows, want_rows[owner], strict=True):
            require(actual.name == want.name and files[actual.definition_id]["id"] == want.definition_id
                    and actual.configuration_name == want.configuration_name and actual.configuration_id == "0"
                    and actual.reference_number == actual.name.rsplit("-", 1)[-1]
                    and not any((actual.suppressed, actual.hidden, actual.fixed, actual.flexible, actual.exclude_from_bom)),
                    "relative occurrence order, ownership, selection, or flags changed")
            local_error = max(local_error, difference(actual.transform.values, want.transform.values))
            instances[actual.id] = ((owner, actual.name), actual)
        actual_numbers = [row.order for row in actual_rows]
        authored_numbers = [row.order for row in want_rows[owner]]
        orders[owner] = {"actual": actual_numbers, "authored": authored_numbers}
    world_error = 0.0
    depths = []
    for actual, want in zip(graph.attributes["flattened_occurrences"], expected_paths, strict=True):
        path, pose = want
        ids = actual["instance_path"]
        require(tuple(instances[key][0] for key in ids) == path and actual["depth"] == len(path) - 1
                and actual["occurrence_id"] == ids[-1] and actual["definition_id"] == instances[ids[-1]][1].definition_id,
                "flattened path, depth, order, or target changed")
        composed = IDENTITY
        for key in ids:
            composed = multiply(composed, instances[key][1].transform.values)
        world_error = max(world_error, difference(composed, pose))
        depths.append(actual["depth"])
    xml_tree = XmlRoot(archive.require(ComponentTreeStream))
    require(local_error <= 1e-12 and world_error <= 1e-12
            and not (graph.mates or graph.mate_groups or document.meshes or graph.attributes["display_states"])
            and xml_tree.find(".//sw:swDisplayStateList", KDisplayNs) is None,
            "assembly placements, mate-free state, or display scope changed")
    require(all(row.kind == "mate-list" and len(row.data) == 6 for row in document.brep_payloads),
            "record retains an unexpected native payload")
    return {"definitions": sorted(files.values(), key=lambda row: row["file"]),
            "direct_occurrences": len(want_rows[owner_id]), "expanded_depths": depths, "orders": orders,
            "public_local_pose_peak_delta": local_error, "public_composed_pose_peak_delta": world_error,
            "physical_direct_occurrences": physical,
            "declared_display_states": 0, "mesh_count": 0, "mate_lists_bytes": [6] * len(document.brep_payloads),
            "nested_guard": refusal(lambda: ReadNestedAsm(document), "ValueError",
                                    "assembly root contains unprojected model content")}


def worker(job):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]
    from AuditNestedNeutralComposition import authored_document
    from convert import open_document, write_document
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyWriting.Nested.WriteNestedAsm import WriteNestedAsm
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-be", "utf-16-le"):
        lookup(encoding)
    folder = Path(job["folder"])
    manifest = job["files"]
    row = manifest[job["owner"]]
    path = folder / row["file"]
    frozen = {folder / item["file"]: item for item in manifest.values()}
    expected, _ = authored_document(job["request"])
    expected.assert_valid()
    expected_def = next(item for item in expected.assembly.definitions if item.id == job["owner"])
    guard = FrozenReads(frozen)
    sys.addaudithook(guard.inspect)
    document = open_document(path)
    document.assert_valid()
    require(document.source.sha256 == row["sha256"] and document.source.container_version == "4",
            "default reader source did not bind the frozen container")
    archive = SldprtArchive.from_bytes(checked(path, row["sha256"], row["bytes"]))
    link = ReadNativeLink(archive, 0)
    header = RequireNode(link.ConfigValue.HeaderValue.FieldsValue["f38"], "moExtObject_c")
    key = ReadFileKey(header)
    selection, = document.configurations
    require(ReadNodeName(link.ConfigValue.RootValue) == expected_def.name
            and key[1] == row["encoded_path"]
            and selection.active and selection.name == expected_def.configuration_name
            and selection.attributes["native_configuration_id"] == 0
            and selection.id == "sldprt:configuration:0", "typed identity or active selection differs")
    values = scope(document)
    if document.assembly is None:
        authored_part, = (item.document for item in expected.assembly.documents
                          if item.id == expected_def.document_id)
        values["part"] = leaf_semantics(document, authored_part)
    else:
        values["assembly"] = assembly_semantics(document, link, archive, expected, job["owner"], manifest, folder)
    output = Path(job["destination"]) / row["file"]
    values["write_refusals"] = {
        "implicit_public": refusal(lambda: write_document(document, output), "AdapterNotFoundError",
                                   "no writer supports the destination"),
        "explicit_public": refusal(lambda: write_document(document, output, destination_format=document.source.format_id),
                                   "ValueError", "native-only feature definitions cannot be exported:"),
    }
    if document.assembly is not None:
        values["write_refusals"]["explicit_internal_nested"] = refusal(
            lambda: WriteNestedAsm(document, output), "ValueError", "native-only feature definitions cannot be exported:")
    require(not guard.denied and not any(name in ("pythoncom", "pywintypes", "Swapp") or name.startswith("win32com")
                                        for name in sys.modules), "worker attempted unexpected file, process, or CAD access")
    guard.active = False
    require(not tuple(output.parent.iterdir()), "failed write published a file or left staging output")
    return {"file": row["file"], "sha256": row["sha256"], "bytes": row["bytes"],
            "typed_root_name": expected_def.name, "archived_file_key_sha256": digest(json.dumps(key).encode()),
            "typed_root_class": link.ConfigValue.RootValue.ClassValue.NameValue,
            "active_config": {"public_id": selection.id, "native_id": 0, "name": selection.name,
                              "attributes": sorted(selection.attributes)},
            "frozen_data_reads": sorted(guard.reads), "denied_access_attempts": 0, **values}


def audit(workspace):
    require(git("rev-parse", "HEAD:src").decode().strip() == SOURCE_TREE
            and not git("status", "--porcelain", "--", "src"),
            "the reader must use the exact clean source tree")
    prior = json.loads(checked(ROOT / PRIOR, PRIOR_SHA))
    authored_sha = digest(git("show", f"{REVISION}:{AUTHOR}"))
    checked(ROOT / AUTHOR, authored_sha)
    require(tuple(row["case"] for row in prior["cases"]) == EXPECTED_CASES, "upstream disclosed cases differ")
    output = {}
    for case in prior["cases"]:
        area = workspace / case["case"]
        fixture = json.loads(checked(area / "Fixture.json", case["fixture_sha256"]))
        request = json.loads(checked(area / "NeutralRequest.json", fixture["request_sha256"]))
        folder = area / "FrozenGenerated"
        require(folder.is_dir() and not folder.is_symlink() and folder.resolve() == folder,
                "frozen case directory must be an actual absolute directory")
        files = fixture["files"]
        require(all(Path(row["file"]).name == row["file"] == PureWindowsPath(row["encoded_path"]).name
                    for row in files.values())
                and {child.name for child in folder.iterdir()} == {row["file"] for row in files.values()},
                "unexpected files in the frozen case directory")
        for row in files.values():
            checked(folder / row["file"], row["sha256"], row["bytes"])
        records = {}
        for owner in files:
            with TemporaryDirectory(prefix="KitNestedReadback") as destination:
                payload = {"owner": owner, "request": request, "folder": str(folder), "destination": destination,
                           "files": files}
                result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(payload),
                             capture_output=True, text=True, timeout=120)
                require(result.returncode == 0 and not result.stderr, result.stderr[-4200:])
                item = json.loads(result.stdout)
                require(item["file"] == files[owner]["file"], "wrong fresh process result")
                records[item["file"]] = item
        for result in records.values():
            for occurrence in result.get("assembly", {}).get("physical_direct_occurrences", ()):
                require(occurrence["external_key_sha256"] == records[occurrence["target"]]["archived_file_key_sha256"],
                        "typed occurrence file key differs from actual child's header")
        for item in files.values():
            checked(folder / item["file"], item["sha256"], item["bytes"])
        output[case["case"]] = {"fixture_sha256": case["fixture_sha256"], "request_sha256": fixture["request_sha256"],
                                 "files_unchanged": True, "native_prior_result_sha256": case["result_sha256"],
                                 "files": records}
    return {"schema": "kit.sw2026.nested-cold-readback.v1", "reader_revision": REVISION, "source_tree": SOURCE_TREE,
            "tool_sha256": digest(HERE.read_bytes()), "authored_projection_sha256": authored_sha,
            "prior_measurement_sha256": PRIOR_SHA, "cases": output,
            "fresh_sdk_processes": sum(len(row["files"]) for row in output.values()),
            "native_processes_started": 0, "private_inputs_opened": 0, "same_format_outputs": 0,
            "native_to_native_reexport_qualified": False}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        require(args.workspace is not None and args.output is not None, "workspace and output paths are required")
        blob = (json.dumps(audit(args.workspace.resolve()), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as target:
            target.write(blob)
        print(digest(blob))
