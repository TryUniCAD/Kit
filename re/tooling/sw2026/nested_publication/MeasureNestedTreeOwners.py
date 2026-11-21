from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path, PureWindowsPath
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(TOOLS), str(TOOLS / "planar_registry")]

from MeasureNestedReadback import FrozenReads, IDENTITY, checked, difference, digest, git, multiply, refusal, require
from PlanarRootProjection import ROOT_CLASSES, keyword_rows, occurrences, read_manager, read_notes, read_scene
from convert import open_document
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import KAsmXmlRoles
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import ReadRigidXform
from convert.adapters.solidworks.Archive.Construction.System.MakeDefaultData import MakeDefaultData
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.IsAnchorFixed import IsAnchorFixed
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.Presentation.DefaultRows import KDefaultMembers, MakeDefaultRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureKinds import NativeFeature

BASIS = "42878d802e4d53ba1dd92528a67fa8122880cff0"
SOURCE_TREE = "8ec147cb733526d1b281923bf3350e15f91c77e3"
MEASURES = ROOT / "re/solidworks/measurements/2026"
PINS = {
    "DisclosedNestedAssemblyArchiveAudit01.json": "4f116aeb6b8d7234bf980390c2ee74086fbfbc0c76efc38f2cfd84183f12631b",
    "NestedAssemblyDisclosedReplayNative01.json": "4253a4ec506d58a421c631f8d9d8cb7a6ce7cba624d54f8e82ebc9814a6f2ae5",
    "SdkNestedNeutralNative01.json": "aa786c6aa4bc7bdae15662c4b4908205b7a0fda7fdb5bb1bb503594a6b0fb967",
}
BOUND_TOOLS = (
    "re/tooling/sw2026/nested_publication/MeasureNestedReadback.py",
    "re/tooling/sw2026/planar_registry/PlanarRootProjection.py",
    "re/tooling/sw2026/para/concentric/ProveConcentricParentExploded.py",
    "re/tooling/sw2026/para/concentric/ProveConcentricParentLights.py",
    "re/tooling/sw2026/para/concentric/ProveConcentricParentNotes.py",
)
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
MODEL_HEADER = "Contents/Config-0-ModelHeader"
MATES = "Contents/Config-0-MatesList"
NO_CHILDREN = {"list": {"n": 0, "items": []}, "tail": 0}
POSE_DELTA = 1e-9


def read_pinned(path, pin, size=None):
    require(path == path.resolve(strict=True), "disclosed locator is redirected")
    return checked(path, pin, size)


def json_digest(value):
    return digest(json.dumps(value, sort_keys=True, allow_nan=False).encode())


def native_case(label, folder, files, owner, phase, evidence, authored_pin, *, generated):
    require(phase["passed"] and phase["open_errors"] == phase["open_warnings"] == 0,
            "native source observation reported an open issue")
    initial = phase["initial"]
    rebuilt = phase["rebuilt"]
    first = initial["definitions"]
    second = rebuilt["definitions"]
    require(set(first) == set(second) == set(files), "native observation has a different file closure")
    for key, row in files.items():
        require(first[key]["sha256"] == second[key]["sha256"] == row["sha256"]
                and first[key]["tree"] == second[key]["tree"],
                "native initial and rebuild trees do not bind the same disclosed file")
    return {"label": label, "folder": str(folder), "files": files, "owner": owner,
            "native_result_sha256": evidence, "author_intent_sha256": authored_pin,
            "native_tree": first[owner]["tree"], "observed_occurrences": initial["occurrences"],
            "generated": generated}


def native_originals(workspace, audit, native):
    path = workspace / "NestedAssemblyReopen01/Inspection/DisclosedNestedReopenResults.json"
    pin = native["raw_native_result_sha256"]
    replay = json.loads(read_pinned(path, pin))
    require(replay["read_only"] and replay["passed"] and replay["controls_healthy"]
            and replay["input_files_unchanged"] and replay["heldout_inputs_read"] == 0
            and replay["oracle_sha256"] == ORACLE and replay["distinct_processes"] == 4,
            "native original replay is outside the closed disclosed cohort")
    for label, owner in (("N01NestedSingle", "SingleFrame"), ("N02MixedRepeated", "MixedFrame")):
        folder = workspace / "NestedAssemblySource01/Results" / label
        row = audit["cases"][label]
        author_pin = native["author_record_sha256"][label]
        require(row["source_author_sha256"] == author_pin, "original author identity differs")
        author = json.loads(read_pinned(folder / "Author.json", author_pin))
        case = author["job"]["case"]
        require(author["passed"] and author["job"]["mode"] == "author" and case["split"] == "discovery"
                and case["name"] == label and case["assemblies"][-1]["name"] == owner,
                "source author record does not describe the disclosed rigid hierarchy")
        files = {}
        for kind, suffix in (("parts", ".SLDPRT"), ("assemblies", ".SLDASM")):
            for definition in case[kind]:
                name = definition["name"]
                source = author["result"]["saved_files"][name]
                prior = row["documents"][name]
                require(source["status"] == [True, 0, 0]
                        and (source["sha256"], source["bytes"]) == (prior["native_sha256"], prior["native_bytes"]),
                        "author and typed audit describe different CAD files")
                files[name] = {"file": name + suffix, "sha256": source["sha256"], "bytes": source["bytes"]}
        phase, = (item for item in replay["phases"] if item["name"] == label and item["mode"] == "reopen")
        require(phase["source_files_unchanged"] and phase["initial"]["root"] == owner,
                "native original root changed at read-only reopen")
        yield native_case(label, folder / "Author", files, owner, phase, pin, author_pin, generated=False)


def generated_cases(workspace, native):
    require(tuple(row["case"] for row in native["cases"]) ==
            ("SdkNestedNeutralNative03", "SdkRepeatedNeutralNative03"), "unexpected generated comparison cohort")
    for prior in native["cases"]:
        label = prior["case"]
        folder = workspace / label
        fixture = json.loads(read_pinned(folder / "Fixture.json", prior["fixture_sha256"]))
        pin = prior["result_sha256"]
        replay = json.loads(read_pinned(folder / "Inspection/Result.json", pin))
        require(replay["passed"] and replay["controls_healthy"] and replay["frozen_inputs_unchanged"]
                and replay["heldout_inputs_read"] == 0 and replay["distinct_processes"] == 4
                and replay["oracle_sha256"] == ORACLE and replay["fixture_sha256"] == prior["fixture_sha256"],
                "generated observation does not bind the exact disclosed qualification")
        author_pin = fixture["request_sha256"]
        request = json.loads(read_pinned(folder / "NeutralRequest.json", author_pin))
        owner = request["root"]
        require(owner == replay["root"] and request["part_tree_profile"] == "neutral_standard"
                and {row["id"] for row in request["definitions"]} == set(fixture["files"]),
                "neutral request does not own the complete native bundle")
        for definition in (row for row in request["definitions"] if row["kind"] == "assembly"):
            require(not definition["request"].get("mates") and not definition["request"].get("lights")
                    and not definition["request"].get("notes"), "generated request has explicit scene or mate intent")
        files = {key: {field: item[field] for field in ("file", "sha256", "bytes")}
                 for key, item in fixture["files"].items()}
        phase, = (item for item in replay["phases"] if item["mode"] == "generated")
        yield native_case(label, folder / "FrozenGenerated", files, owner, phase, pin, author_pin, generated=True)


def pose_words(basis, origin):
    return tuple(component for axis in range(3) for component in
                 (basis[axis], basis[axis + 3], basis[axis + 6], 1000 * origin[axis])) + (0, 0, 0, 1)


def require_directory_alias(link, external):
    def slots(mapping):
        return tuple(entry.IndexValue for entry in mapping.EntriesValue if entry.EntryValue is external)

    indices = slots(link.ConfigValue.MapValue)
    require(len(indices) == 1 and slots(link.ResolvedValue.MapValue) == indices,
            "linked occurrence external file lost its actual configuration directory slot")


def compare_occurrences(document, links, file_keys, observed, root):
    graph = document.assembly
    by_owner = {row.id: {} for row in graph.definitions}
    by_id = {row.id: row for row in graph.instances}
    by_feature = {}
    for row in graph.instances:
        names = by_owner[row.owner_definition_id]
        require(row.name not in names and not (row.hidden or row.suppressed or row.flexible or row.exclude_from_bom),
                "assembly has a duplicate or nonrigid occurrence")
        names[row.name] = row
    definitions = {row.id: Path(row.source_path).name for row in graph.definitions}
    require(definitions[graph.root_definition_id] == root, "public reference graph has a different root")
    require(len(definitions) == len(file_keys) and set(definitions.values()) == set(file_keys),
            "public reference graph does not match the verified physical definitions")
    peak = 0.0
    for owner, names in by_owner.items():
        link = links.get(definitions[owner])
        if link is None:
            require(not names, "part definition owns an assembly occurrence")
            continue
        model = RequireNative(link.ConfigValue.RootValue, "moAssembly_c")
        refs = occurrences(model)
        CheckTreeAlias(link, refs)
        require(model.FieldsValue["f1560"] == len(refs) == len(names)
                and {ReadNativeName(node) for node in refs} == set(names),
                "binary direct references and public occurrences differ")
        for node in refs:
            row = names[ReadNativeName(node)]
            fields = node.FieldsValue
            cfg = fields["f3c0"]
            external = RequireNative(fields["f3b0"], "moExtObject_c")
            require_directory_alias(link, external)
            path = definitions[row.definition_id]
            require(row.attributes["native_feature_id"] == NativeNodeId(node)
                    and cfg == {"f08": row.configuration_name, "f10": int(row.configuration_id)}
                    and ReadFileKey(external) == file_keys[path]
                    and IsAnchorFixed(node, row.name) == row.fixed,
                    "occurrence has a different physical alias target, configuration or fixed owner")
            local = pose_words(*ReadRigidXform(fields["f360"]))
            peak = max(peak, difference(local, row.transform.values))
            by_feature[(owner, NativeNodeId(node))] = row.id
    require(len(by_feature) == len(graph.instances) == len(by_id) and peak <= POSE_DELTA,
            "nonunique typed occurrence map or different local transform")
    found = {}
    worst = 0.0

    def visit(owner, rows, path=(), pose=IDENTITY):
        nonlocal worst
        want = by_owner[owner]
        require(len(rows) == len(want), "native scene has a different child count")
        for item in rows:
            native_name = item["name"].rsplit("/", 1)[-1]
            row = want[native_name]
            effective = multiply(pose, row.transform.values)
            world = item["world"]
            require(len(world) == 16 and world[12:] == [1.0, 0.0, 0.0, 0.0]
                    and (definitions[row.definition_id], row.configuration_name, row.fixed)
                    == (item["file"], item["configuration"], item["fixed"]),
                    "native scene targets a different file, configuration or rigid occurrence")
            worst = max(worst, difference(effective, pose_words(world[:9], world[9:12])))
            indices = (*path, row.id)
            require(indices not in found, "native scene expands the same instance path twice")
            found[indices] = (row.id, row.definition_id, len(indices) - 1)
            visit(row.definition_id, item["children"], indices, effective)

    visit(graph.root_definition_id, observed)
    expanded = graph.attributes["flattened_occurrences"]
    public_paths = {tuple(row["instance_path"]): (row["occurrence_id"], row["definition_id"], row["depth"])
                    for row in expanded}
    require(found == public_paths and len(found) == len(expanded) and worst <= POSE_DELTA,
            "decoded occurrence paths or composed rigid transforms differ from the native scene")
    return {"definitions": len(definitions), "direct_links": len(by_feature),
            "expanded_occurrences": len(found), "expanded_depth_counts": dict(Counter(item[2] for item in found.values())),
            "maximum_local_matrix_delta": peak, "maximum_native_world_matrix_delta": worst}


def linked_empty_mates(archive, link):
    group, = (item for item in link.ResolvedValue.RootsValue if item.ClassValue.NameValue == "moMateGroup_c")
    fields = group.FieldsValue
    require(fields["f60"] == NO_CHILDREN and not fields["discarded_manager_records"] and not fields["f4e8"],
            "resolved mate group contains independently owned members")
    raw = archive.require(MATES)
    graph = ReadMatesMut(raw, link.ResolvedValue)
    require(len(raw) == 6 and not graph.RootsValue and graph.ReportValue["completed"]
            and graph.MapValue == link.ResolvedValue.MapValue,
            "resolved empty mate group has a populated or detached linked mate list")
    CheckTreeAlias(link, (group,))
    return {"native_id": NativeNodeId(group), "span": dict(NativeNodeSpan(link, group)),
            "linked_map_base": graph.MapBase, "linked_payload_sha256": digest(raw)}


def normalize_tree(rows):
    require(all(row["error"] == 0 and not row["warning"] and not row["suppressed"] for row in rows),
            "native feature observer reported a suppressed or unhealthy tree row")
    return Counter((row["name"], row["type"], row["parent"]) for row in rows)


def verify_tree_observation(projected, observed):
    require(len(projected) == len(observed) and Counter(projected) == normalize_tree(observed),
            "typed root/member hierarchy differs from the native feature observer")


def native_type(node):
    return node.ClassValue.NameValue.removeprefix("mo").removesuffix("_c")


def principal_support(roots):
    front, top, right = (node for node in roots if node.ClassValue.NameValue == "moRefPlane_c")
    for axis, plane in zip(("z", "y", "x"), (front, top, right), strict=True):
        fields = RequireNative(plane.FieldsValue["f6f8"], "moDefaultRefPlnData_c").FieldsValue
        frame = PrincipalFrame(axis)
        expected = MakeDefaultData(axis, frame).FieldsValue
        require(ReadVector(fields["root"]) == frame.OriginValue
                and ReadVector(fields["normal"]) == frame.NormalValue
                and ReadRigidXform(fields["f20"]) == ReadRigidXform(expected["f20"]),
                "assembly principal datum differs from its canonical geometry")
    origin, = (node for node in roots if node.ClassValue.NameValue == "moOriginProfileFeature_c")
    fields = origin.FieldsValue
    ref = RequireNative(fields["pd_f78"], "moCompRefPlane_c").FieldsValue
    sketch = RequireNative(fields["pd_f80"], "sgSketch").FieldsValue
    point, = sketch["points"]
    require(ref["ff0"]["f00"] == NativeNodeId(front) and sketch["npoints"] == 1 and point["kind"] == 0
            and point["point"]["pos"] == {"x": 0.0, "y": 0.0},
            "assembly origin is not the typed point on the actual front plane")
    return {"principal_plane_ids": [NativeNodeId(node) for node in (front, top, right)], "origin_id": NativeNodeId(origin)}


def inspect_root(document, archive, link, observed, *, generated):
    model = RequireNative(link.ConfigValue.RootValue, "moAssembly_c")
    roots = tuple(RequireNative(item) for item in link.ResolvedValue.RootsValue)
    require(tuple(node.ClassValue.NameValue for node in roots) == ROOT_CLASSES,
            "the assembly has a nonordinary resolved root class")
    datum_owners = principal_support(roots)
    environment, lights, inputs = read_scene(link, empty=generated)
    cabinet, notes, note_inputs = read_notes(link, 0 if generated else 2)
    manager = read_manager(link, present=not generated)
    refs = occurrences(model)
    owners = {"resolved_root": roots, "environment_member": lights, "cabinet_member": notes,
              "exploded_manager": () if manager is None else (manager,), "occurrence_alias": refs}
    all_nodes = tuple(node for children in owners.values() for node in children)
    CheckTreeAlias(link, all_nodes)
    require(len({NativeNodeId(node) for node in all_nodes}) == len(all_nodes)
            and all(not ReadChildren(node) for node in roots if node is not environment and node is not cabinet),
            "assembly has duplicated persistent IDs or an unrepresented root child")
    spans = {NativeNodeId(node): dict(NativeNodeSpan(link, node)) for node in all_nodes}
    for node in all_nodes:
        span = spans[NativeNodeId(node)]
        require(0 <= span["offset"] < span["end"] <= len(archive.require(span["stream"])),
                "typed owner lacks a complete physical interval")
    classes = {NativeNodeId(node): node.ClassValue.NameValue for node in all_nodes}
    index = keyword_rows(archive, owners, document)
    require(all(isinstance(row.definition, NativeFeature) for row in document.feature_timeline),
            "public root has an unexpected native feature projection")
    for row in index:
        cls = classes[row["id"]]
        tag, kind = ("Reference", "Reference") if cls == "moReference_c" else KAsmXmlRoles[cls]
        expected = kind if tag == "Feature" else tag
        require((row["keyword_tag"], row["keyword_type"].casefold()) == (tag, expected.casefold()),
                "keyword type differs from its typed owner role")
    projection = [(ReadNativeName(node), native_type(node), None) for node in (*roots, *refs)]
    implicit = []
    for parent, members in ((environment, lights), (cabinet, notes)):
        parent_id = NativeNodeId(parent)
        default = KDefaultMembers[parent.ClassValue.NameValue]
        if members:
            require(tuple((ReadNativeName(node), node.ClassValue.NameValue) for node in members) ==
                    tuple((name, cls) for _, name, cls in default),
                    "real nested member changes the ordinary default role profile")
            for member in members:
                span, owning = spans[NativeNodeId(member)], spans[parent_id]
                require(span["stream"] == owning["stream"]
                        and owning["offset"] <= span["offset"] < span["end"] <= owning["end"],
                        "member interval does not belong to its actual owner")
                projection.append((ReadNativeName(member), native_type(member), ReadNativeName(parent)))
        else:
            defaults = MakeDefaultRows(parent)
            require(all(row["native_object_id"] is None and row["typed_archive_owner"] is None for row in defaults),
                    "implicit runtime support was assigned an invented stored ID")
            projection.extend((row["name"], row["type"], row["parent"]) for row in defaults)
            implicit.extend(row["owner_role"] for row in defaults)
    verify_tree_observation(projection, observed)
    require(not document.assembly.mate_groups and not document.assembly.mates,
            "public empty mate state has unrepresented semantic constraints")
    detached = replace(refs[0])
    repeated = replace(document, feature_timeline=(*document.feature_timeline[:-1], document.feature_timeline[0]))
    member = next(row for row in projection if row[2] is not None)
    reparented = [row if row != member else (*member[:2], None) for row in projection]
    refusals = {
        "detached_map_alias": refusal(lambda: CheckTreeAlias(link, (detached,)), "ValueError",
                                       "through-all presentation owner does not alias its archive map"),
        "duplicate_public_id": refusal(lambda: keyword_rows(archive, owners, repeated), "ValueError",
                                       "normal feature identities differ from the actual keyword index"),
        "wrong_member_parent": refusal(lambda: verify_tree_observation(reparented, observed), "ValueError",
                                        "typed root/member hierarchy differs from the native feature observer"),
    }
    lighting = [{key: value for key, value in asdict(row).items() if key != "CreatedValue"} for row in inputs]
    return {"native_only_public_rows": len(index), "visible_native_rows": len(projection),
            "unmatched_public_owners": 0, "unmatched_visible_rows": 0,
            "canonical_datum_owners": datum_owners,
            "owners": {role: [NativeNodeId(node) for node in nodes] for role, nodes in owners.items()},
            "owner_binding_sha256": json_digest(spans),
            "native_state_sha256": json_digest(sorted(projection, key=str)),
            "runtime_only_roles": implicit, "index_only_manager": None if manager is None else NativeNodeId(manager),
            "stored_light_intent_sha256": json_digest(lighting) if lighting else None,
            "stored_empty_notes": note_inputs is not None, "refusals": refusals}


def pin_observed(rows, manifest):
    return [{"file": manifest[row["target"]]["file"], "children": pin_observed(row["children"], manifest),
             **{key: row[key] for key in ("name", "configuration", "fixed", "world")}} for row in rows]


def worker(job):
    folder = Path(job["folder"])
    manifest = job["files"]
    require(all(Path(row["file"]).name == row["file"] and Path(row["file"]).suffix in (".SLDASM", ".SLDPRT")
                for row in manifest.values()) and len({row["file"] for row in manifest.values()}) == len(manifest),
            "disclosed directory describes a nonlocal or duplicate file")
    source = {folder / row["file"]: row for row in manifest.values()}
    raw = {path.name: read_pinned(path, row["sha256"], row["bytes"]) for path, row in source.items()}
    filename = manifest[job["owner"]]["file"]
    for encoding in ("utf-16-le", "cp1252"):
        lookup(encoding)
    guard = FrozenReads(source)
    sys.addaudithook(guard.inspect)
    document = open_document(folder / filename)
    docs = {Path(item.document.source.path).name: item.document.source.sha256 for item in document.assembly.documents}
    require(document.source.sha256 == manifest[job["owner"]]["sha256"]
            and docs == {path.name: row["sha256"] for path, row in source.items() if path.name != filename},
            "strict linked read resolved a different native file closure")
    archives = {name: SldprtArchive.from_bytes(data) for name, data in raw.items()}
    linked = {name: ReadNativeLink(archive, 0) for name, archive in archives.items() if name.endswith(".SLDASM")}
    file_keys = {name: ReadFileKey(RequireNative(ReadHeaderGraph(archive.require(MODEL_HEADER), 19000)
                                                   .FieldsValue["f38"], "moExtObject_c"))
                 for name, archive in archives.items()}
    require(all(PureWindowsPath(key[1]).name.casefold() == name.casefold() for name, key in file_keys.items()),
            "actual native self header has a different filename")
    hierarchy = compare_occurrences(document, linked, file_keys, pin_observed(job["observed_occurrences"], manifest), filename)
    mates = {name: linked_empty_mates(archives[name], link) for name, link in linked.items()}
    tree = inspect_root(document, archives[filename], linked[filename], job["native_tree"], generated=job["generated"])
    require(not guard.denied and guard.reads == {path.name for path in source}
            and not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "guarded inspection missed a file or attempted an unauthorized CAD/data access")
    guard.active = False
    for path, row in source.items():
        read_pinned(path, row["sha256"], row["bytes"])
    open_domains = {
        "assembly_display_state_count": len(document.assembly.attributes["display_states"]),
        "visual_states_bytes": len(archives[filename].streams.get("ThirdPtyStore/VisualStates", b"")),
        "retained_mate_payload_count": len(document.brep_payloads),
        "original_source_metadata": "solidworks_source_bytes" in document.metadata,
    }
    return {"case": job["label"], "root_file": filename, "authority": "generated" if job["generated"] else "native_disclosed",
            "root_file_sha256": manifest[job["owner"]]["sha256"], "native_result_sha256": job["native_result_sha256"],
            "author_intent_sha256": job["author_intent_sha256"], "files_unchanged": True,
            "verified_file_count": len(raw), "guard_denials": 0, "hierarchy": hierarchy, "empty_mates": mates,
            "other_retained_domains": open_domains, **tree}


def measure(workspace):
    require(git("rev-parse", "HEAD:src").decode().strip() == SOURCE_TREE
            and not git("status", "--porcelain", "--", "src"), "the SDK must match the exact clean source tree")
    tools = {path: digest(git("show", f"{BASIS}:{path}")) for path in BOUND_TOOLS}
    for name, digest_value in tools.items():
        read_pinned(ROOT / name, digest_value)
    audit, disclosed, generated = (json.loads(read_pinned(MEASURES / name, pin)) for name, pin in PINS.items())
    jobs = (*native_originals(workspace, audit, disclosed), *generated_cases(workspace, generated))
    cases = []
    for job in jobs:
        result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(job),
                     text=True, capture_output=True, timeout=90)
        require(result.returncode == 0 and not result.stderr, result.stderr[-4600:] or "underived worker output")
        row = json.loads(result.stdout)
        require(row["case"] == job["label"], "mismatched guarded worker")
        cases.append(row)
    require(tuple(row["visible_native_rows"] for row in cases) == (23, 25, 23, 25)
            and len({row["stored_light_intent_sha256"] for row in cases[:2]}) == 1,
            "the disclosed cohorts do not bind both measured default and persisted-state profiles")
    return {"schema": "kit.sw2026.nested-tree-owners.v1", "reader_revision": BASIS, "source_tree": SOURCE_TREE,
            "tool_sha256": digest(HERE.read_bytes()), "prior_receipts_sha256": PINS,
            "prior_tools_sha256": tools,
            "fresh_guarded_processes": len(cases), "native_processes_started": 0, "private_inputs_opened": 0,
            "binary_outputs_created": 0, "native_reexport_qualified": False, "cases": cases}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        report = worker(json.load(sys.stdin))
    else:
        require(args.disclosed is not None and args.disclosed.is_absolute(), "use the absolute disclosed workspace locator")
        report = measure(args.disclosed)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
