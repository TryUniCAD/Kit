from __future__ import annotations

import argparse
import json
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from pathlib import Path, PureWindowsPath

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parents[1]))
sys.path.insert(0, str(SCRIPT.parents[4] / "src"))

from AuthorCurves import digest, require
from Classes import registry
from Core import DOCUMENT_VERSION_2026, Obj
from NestedAssemblySourcePlan import CONTROL_SHA, IDENTITY, ORACLE, checked, compose, expected_tree, matches_transform, placed_point
from ReplayNestedAssemblyReopen import AUTHORED, DISCLOSED, SCHEMA as REPLAY_SCHEMA, source_cases
from RoundTrip import PLANS, stream_roundtrip, usage_summary
from SyncedAssemblies import typed_header
from builders.Assembly import bounding_box
from builders.AssemblyOccurrences import assembly_occurrence_bounds
from builders.Sketch import PlaneFrame
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved, store_resolved
from convert.adapters.solidworks.Assembly.Assembly import Configurations, ExpandItemPaths, Files, Models, XmlRoot
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KComponentTreeStream


VERSION = DOCUMENT_VERSION_2026
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
HEADER = CONFIG + "-ModelHeader"
MANAGER = "Contents/CMgr"
MANAGER_HEADER = "Contents/CMgrHdr2"
STREAMS = (HEADER, "Header2", CONFIG, RESOLVED, MANAGER, MANAGER_HEADER)
UNSELECTED = {"f08": "", "f10": -1}
REPLAY_SHA = "ca4ab515e936a605a98c8fbd093659577c485529d6b0c916dd08683f7ef19ca8"


@dataclass
class Document:
    name: str
    archive: SldprtArchive
    model: Obj
    header: Obj
    top_header: Obj
    config: Obj
    manager_header: Obj
    config_header: Obj
    config_map: object
    resolved_map: object
    resolved_roots: list
    checks: dict

    @property
    def assembly(self):
        return self.model.cls == "moAssembly_c"

    @property
    def box(self):
        return self.model["f1a18" if self.assembly else "f7f8"]


def typed(node, cls):
    require(isinstance(node, Obj) and node.cls == cls, f"missing typed {cls} owner")
    return node


def read_document(path, info, reg):
    archive = SldprtArchive.from_bytes(path.read_bytes(), path)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION, "unexpected source release")
    reports = {stream: stream_roundtrip(archive, stream, reg, {**PLANS, **reg.plans}, linked=True) for stream in STREAMS}
    require(all(row["passed"] for row in reports.values()), f"linked stream round trip differs for {path.name}")
    config_doc, config_map = load_config(archive.require(CONFIG), reg, VERSION, archive=archive, name=CONFIG)
    resolved, resolved_map = load_resolved(archive.require(RESOLVED), reg, VERSION, archive=archive, name=RESOLVED, seed=config_map.map_state())
    projected, seed = store_config_state(config_doc, reg, VERSION)
    require(projected == archive.require(CONFIG) and store_resolved(resolved, reg, VERSION, seed=seed) == archive.require(RESOLVED),
            "resolved round trip does not continue the re-emitted configuration map")
    model, = config_doc.roots
    is_assembly = path.suffix.upper() == ".SLDASM"
    typed(model, "moAssembly_c" if is_assembly else "moPart_c")
    manager = typed_header(archive, reg, MANAGER, "moConfigurationMgr_c")
    config = typed(manager["f360"], "moConfiguration_c" if is_assembly else "moPartConfiguration_c")
    manager_header = typed_header(archive, reg, MANAGER_HEADER, "dmConfigMgrHeader_c")
    config_row, = manager_header["f08"]["items"]
    config_header = typed(config_row["o"], "dmConfigHeader_c")
    require(resolved.head["context"]["model_is_part"] == int(not is_assembly) and
            resolved.head["context"]["cmgr_f658"] == manager["f658"], "resolved stream selects a different model context")
    summary = {stream: {key: row[key] for key in ("sha256", "bytes", "map_base", "map_count", "tail")} |
               {"schema_usage": {key: {"provisional": item["provisional_schemas"], "raw_operations": item["raw_operation_count"]}
                                 for key, item in usage_summary([row]).items()}}
               for stream, row in reports.items()}
    return Document(path.stem, archive, model, config_doc.head["model_header"], typed_header(archive, reg, "Header2", "moHeader_c"),
                    config, manager_header, config_header, config_map, resolved_map, resolved.roots,
                    {"native_sha256": info["sha256"], "native_bytes": info["bytes"], "class": model.cls, "streams": summary})


def file_identity(shared):
    return (PureWindowsPath(shared["h18"]["f08"]), shared["h10"]["f08"], shared["f20"], shared["f28"])


def config_identity(config):
    return {"f08": config["f18"]["f08"], "f10": config["f08"]}


def external_state(entry):
    typed(entry, "moExtObject_c")
    return (file_identity(entry["shared"]), entry["refcfg"], *(entry[key] for key in ("f48", "f4c", "f50", "f54", "f58", "f60", "f70", "f78")))


def header_directory(header):
    listing = header["f30"]
    if listing is None:
        return []
    rows = typed(listing, "moExtObjectList_c")["items"]
    return [typed(row["o"], "moExtObject_c") for row in rows]


def check_headers(doc, expanded, saved):
    header = doc.header
    other = doc.top_header
    require([header[k] for k in ("f40", "f48", "fc4")] == [other[k] for k in ("f40", "f48", "fc4")] and header["fc4"] == expanded,
            "header count or modification state differs")
    require(external_state(header["f38"]) == external_state(other["f38"]) and
            list(map(external_state, header_directory(header))) == list(map(external_state, header_directory(other))), "the two file directories disagree")
    name = doc.model["f18"]["f08"]
    path, stem, kind, creation = file_identity(header["f38"]["shared"])
    selected = config_identity(doc.config)
    require(path.stem == doc.name == stem == name and kind == (3 if doc.assembly else 2) and header["f38"]["refcfg"] == selected and
            header["f38"]["f78"] == -1, "native self ownership differs")
    row = doc.config_header
    require(row["f10"] == selected["f08"] and row["f30"] == selected["f10"] and (row["f44"] & 0xFFFFFFFF) == doc.config["f4c4"] and
            row["f38"] == doc.config["f860"] == header["f40"] == saved["update_stamp"] and doc.manager_header["f60"] == header["f38"]["f60"],
            "configuration summary does not match the active native configuration")
    return {"fc4_expanded_occurrences": expanded, "f40_update_stamp": header["f40"], "f48_modification_time": header["f48"],
            "f28_creation_time": creation, "self_f60_file_time": header["f38"]["f60"], "cmgrhdr2_f60_save_time": doc.manager_header["f60"],
            "configuration_id": selected["f10"], "configuration_flags": doc.config["f4c4"]}


def map_bindings(doc, directory, refs):
    objects = (doc.header["f38"], *directory)
    cfg_map, res_map = doc.config_map, doc.resolved_map
    offsets = range(cfg_map.base - len(objects), cfg_map.base)
    slots = {id(node): index for index, node in zip(offsets, objects, strict=True)}
    refs_by_id = {id(node) for node in refs}
    ref_slots = {id(entry[1]): number for number, entry in cfg_map.table.items() if entry[0] == "obj" and id(entry[1]) in refs_by_id}
    require(len(ref_slots) == len(refs) and res_map.base == cfg_map.count, "resolved map does not inherit the Config-0 placements")
    inherited = slots | ref_slots
    for node in (*objects, *refs):
        number = inherited[id(node)]
        require(cfg_map.table[number][1] is res_map.table[number][1] is node, "resolved map changes the owning Config-0 object identity")
    return slots, ref_slots


def directory_checks(directory, refs, documents, slots):
    uses = Counter(ref["f3b0"]["shared"]["h10"]["f08"] for ref in refs)
    require([entry["shared"]["h10"]["f08"] for entry in directory] == list(uses), "file directory is not the direct target set")
    report = []
    for index, (name, entry) in enumerate(zip(uses, directory, strict=True)):
        child = documents[name]
        require(file_identity(entry["shared"]) == file_identity(child.header["f38"]["shared"]) and entry["f78"] == index and
                entry["f48"] == uses[name] and all(entry[key] == 0 for key in ("f4c", "f50", "f54", "f58")) and entry["refcfg"] == UNSELECTED and
                entry["f60"] == child.header["f38"]["f60"] and entry["f70"] == child.manager_header["f60"], "direct directory target state differs")
        report.append({"target": name, "kind": entry["shared"]["f20"], "f78_index": index, "f48_uses": uses[name], "map_slot": slots[id(entry)],
                       "f60_file_time": entry["f60"], "f70_save_time": entry["f70"]})
    return report


def occurrence_transform(reference):
    require(reference["has_f360"] == 1, "ordinary occurrence has no stored transform")
    xform = reference["f360"]
    require(xform["f70"] == 1.0 and xform["f78"] == 0 and xform["has_matrix"] in (0, 1), "unsupported occurrence transform state")
    basis = tuple(xform["f08"][f"m{i}"] for i in range(9)) if xform["has_matrix"] else tuple(IDENTITY[:9])
    return (*basis, xform["f58"], xform["f60"], xform["f68"], 1.0, 0.0, 0.0, 0.0)


def occurrence_checks(doc, refs, records, expected, documents, states, slots, ref_slots):
    require(len({ref["f08"] for ref in refs}) == len(refs), "ordinary direct occurrence feature ids collide")
    rows = []
    for ref, plan in zip(refs, expected, strict=True):
        child = documents[plan["target"]]
        source = ref["f3b0"]
        require(id(source) in slots and any(source is node for node in records) and file_identity(source["shared"]) == file_identity(child.header["f38"]["shared"]) and
                ref["f3c0"] == config_identity(child.config), "occurrence resolves to a different directory or configuration")
        feature = typed(ref["f4f8"], "moExtFeature_c")
        require(feature["f50"] is ref and feature["f44"] == ref["f08"] and feature["f38"]["f08"] == ref["f18"]["f08"] and
                file_identity(feature["f10"]) == file_identity(doc.header["f38"]["shared"]), "Config-0 occurrence backlink differs")
        geometry, transform = states[child.name]["stamp_pair"]
        require((ref["f3e0"], ref["f3e8"], ref["f3f4"], ref["f3f8"]) == (child.header["f40"], child.header["f48"], geometry, transform) and
                ref["f3f0"] == 102 and ref["f4b0"] == -1, "direct occurrence update state differs")
        require(matches_transform(occurrence_transform(ref), plan["local"]), "stored local occurrence transform differs from its authored placement")
        require(ref["has_f370"] and box_bytes(ref["f370"]) == box_bytes(child.box), "occurrence bounds are not the target-local box")
        rows.append({"feature_id": ref["f08"], "target": child.name, "map_slot": ref_slots[id(ref)], "directory_slot": slots[id(source)],
                     "child_config_id": child.config["f08"], "stamps": {key: ref[key] for key in ("f3e0", "f3e8", "f3f0", "f3f4", "f3f8")},
                     "f4b0": ref["f4b0"], "f370_target_local_exact": True})
    return rows


def cmgr_checks(doc, refs, documents):
    config = doc.config
    self_row, *rows = [typed(row["o"], "moConfigObject_c") for row in config["fce8"]]
    require(self_row["f10"] is None and self_row["f28"] == UNSELECTED and config["fc48"] is not config["fc50"], "configuration self row or option ownership differs")
    defaults_equal = config["fc48"].f == config["fc50"].f
    options, contexts = [self_row["f08"]], []
    for row, ref in zip(rows, reversed(refs), strict=True):
        context = typed(row["f10"], "moContextChainComponent_c")
        chain = typed(context["f20"], "moReferenceChain_c")
        targets = typed(chain["f08"], "moExtFeatureList_c")
        leaf, = [typed(item["o"], "moExtFeature_c") for item in targets["f08"]]
        require(targets["n"] == 1 and chain["f40"] == leaf["f18"] == UNSELECTED and leaf["f44"] == ref["f08"] and
                leaf["f38"]["f08"] == ref["f18"]["f08"] and leaf["f50"] is None and file_identity(leaf["f10"]) == file_identity(ref["f4f8"]["f10"]),
                "CMgr contextual path does not bind the same direct occurrence as Config-0")
        own_file = typed(context["f40"], "moExtObject_c")
        require(own_file["refcfg"] == config_identity(config) and own_file["shared"]["f20"] == 3 and
                own_file["shared"]["f28"] == doc.header["f38"]["shared"]["f28"] and context["f30"] == ((101 + ref["f3f0"]) & 0xFFFFFFFF),
                "CMgr contextual owner or transform stamp differs")
        child = documents[ref["f3b0"]["shared"]["h10"]["f08"]]
        option_field = "fc48" if child.assembly else "fc50"
        selected = typed(row["f08"], "moConfig_c")
        require(row["f28"] == config_identity(child.config) and selected is not config[option_field], "CMgr option or target selection differs")
        options.append(selected)
        contexts.append({"feature_id": leaf["f44"], "chain_length": targets["n"], "f30_stamp": context["f30"],
                         "target_option_field_from_native_dispatch": option_field,
                         "saved_option_deltas": sorted(key for key, value in config[option_field].f.items() if selected[key] != value),
                         "containing_file_name_equal": own_file["shared"]["h10"]["f08"] == doc.name})
    require(len({id(option) for option in options}) == len(options), "CMgr placement options alias")
    return {"self_first": True, "default_option_values_equal": defaults_equal, "rows": contexts}


def box_words(box):
    return tuple(box[f"b{index}"] for index in range(10))


def box_bytes(box):
    return struct.pack("<10d", *box_words(box))


def box_extents(box):
    return tuple(box[f"b{index}"] for index in (6, 7, 8, 3, 4, 5))


def deltas(actual, predicted):
    return max(abs(first - second) for first, second in zip(actual, predicted, strict=True))


def leaf_extents(leaves):
    points = [placed_point(point, pose) for box, pose in leaves
              for point in product(*((box[f"b{i + 6}"], box[f"b{i + 3}"]) for i in range(3)))]
    axes = tuple(zip(*points, strict=True))
    return (*(min(axis) for axis in axes), *(max(axis) for axis in axes))


def bounds_checks(doc, refs, rows, states):
    require(doc.model["has_f1a18"] == doc.model["has_f1a20"] == 1, "both saved assembly boxes are required")
    poses = [occurrence_transform(ref) for ref in refs]
    frames = [PlaneFrame(origin=pose[9:12], u=pose[:3], v=pose[3:6]) for pose in poses]
    projected = assembly_occurrence_bounds(occurrences=zip(refs, frames, strict=True))
    leaves = [(box, compose(nested, pose)) for row, pose in zip(rows, poses, strict=True)
              for box, nested in states[row["target"]]["leaves"]]
    flattened = leaf_extents(leaves)
    errors = {}
    for field in ("f1a18", "f1a20"):
        boxed = doc.model[field]
        extrema = box_extents(boxed)
        naive_sphere = bounding_box(minimum=extrema[:3], maximum=extrema[3:])
        errors[field] = {
            "direct_fold_max_abs_delta_m": deltas(box_words(boxed), box_words(projected)),
            "direct_fold_exact": box_bytes(boxed) == box_bytes(projected),
            "flat_leaves_extents_max_abs_delta_m": deltas(extrema, flattened),
            "aabb_radius_abs_delta_m": abs(boxed["b9"] - naive_sphere["b9"]),
        }
        require(errors[field]["direct_fold_max_abs_delta_m"] < 5e-15, "direct child bounds fold differs from saved assembly box")
    return ({"present": [1, 1], "two_boxes_byte_equal": box_bytes(doc.model["f1a18"]) == box_bytes(doc.model["f1a20"]),
             "f1a28": doc.model["f1a28"], "comparisons": errors}, leaves)


def stamps_for(doc, refs, rows, states):
    geometry = doc.model["f1300"]
    transform = 101
    for ref, row in zip(refs, rows, strict=True):
        geometry = (geometry + states[row["target"]]["stamp_pair"][0]) & 0xFFFFFFFF
        own_transform = ref["f3f0"]
        transform = own_transform if transform == 101 else (transform + own_transform) & 0xFFFFFFFF
    expected = (geometry, transform)
    require(expected == (doc.config_header["f50"], doc.config_header["f4c"]), "recomputed stamps differ from CMgrHdr2")
    return expected


def local_rows(doc, state, documents, by_id, xml_items):
    direct = [item for item in xml_items if by_id[item.owner_definition_id] == doc.name]
    refs = state["refs"]
    for ref, row, item in zip(refs, state["rows"], direct, strict=True):
        target = documents[row["target"]]
        pose = occurrence_transform(ref)
        transform = (*pose[:3], 0, *pose[3:6], 0, *pose[6:9], 0, *pose[9:12], 1)
        require(item.feature_id == ref["f08"] and by_id[item.definition_id] == target.name and
                f"{item.name}-{item.reference_number}" == ref["f18"]["f08"] and item.transform_stamp == ref["f3f0"] and
                (item.configuration_name, item.configuration_id) == (target.config["f18"]["f08"], target.config["f08"]) and
                dict(item.attributes)["swTransform"] == " ".join(format(value, ".16g") for value in transform),
                "XML direct occurrence does not project its binary placement")
    return len(direct)


def expanded_binary(owner, states):
    for row in states[owner]["rows"]:
        target = row["target"]
        yield (owner, row["feature_id"], target)
        yield from expanded_binary(target, states)


def xml_checks(doc, documents, states):
    data = doc.archive.require(KComponentTreeStream)
    xml = XmlRoot(data)
    files = Files(xml)
    configs = Configurations(xml)
    selected, = configs
    defs, occs = Models(xml, {item.object_id: item for item in files})
    names = {item.object_id: PureWindowsPath(item.source_path).stem for item in defs}
    require(xml.attrib["swVersion"] == str(VERSION) and names[selected.model_id] == doc.name and
            (selected.name, selected.configuration_id) == (doc.config["f18"]["f08"], doc.config["f08"]), "XML root configuration differs")
    expanded = tuple(expanded_binary(doc.name, states))
    closure = {doc.name, *(target for _, _, target in expanded)}
    require(len(files) == len(defs) == len(closure) and set(names.values()) == closure, "XML is missing a transitive definition")
    for entry in files:
        path = PureWindowsPath(entry.source_path)
        source_file, _, kind, created = file_identity(documents[path.stem].header["f38"]["shared"])
        require(path == source_file and entry.document_type == ("ASSEMBLY" if kind == 3 else "PART") and entry.creation_time == created,
                "XML file identity differs from the linked self record")
    count_by_definition = {}
    for entry in defs:
        target = documents[names[entry.object_id]]
        require((entry.configuration_name, entry.configuration_id) == (target.config["f18"]["f08"], target.config["f08"]) and
                (entry.configuration_flags & 0xFFFFFFFF) == target.config["f4c4"] and entry.last_modified_stamp == target.config["f860"],
                "XML configuration metadata differs from its native source")
        box = " ".join(format(value, ".16g") for value in box_extents(target.box)) if target.assembly else None
        require(dict(entry.attributes).get("swBoundingBox") == box, "XML bounding box does not project its owner-local axis limits")
        count_by_definition[target.name] = local_rows(target, states[target.name], documents, names, occs)
    paths = ExpandItemPaths(selected.model_id, defs, occs)
    items = {item.object_id: item for item in occs}
    projected = tuple((names[items[path.occurrence_id].owner_definition_id], items[path.occurrence_id].feature_id, names[path.definition_id]) for path in paths)
    require(projected == expanded and len({path.path for path in paths}) == len(expanded), "expanded occurrence XML differs from binary hierarchy")
    return {"files": len(files), "definitions": len(defs), "definition_local_occurrences": len(occs), "expanded_occurrence_paths": len(paths),
            "definition_direct_counts": count_by_definition, "bytes": len(data), "sha256": sha256(data).hexdigest()}


def audit_case(case, paths, author, reg):
    documents = {name: read_document(path, author["saved_files"][name], reg) for name, path in paths.items()}
    states = {}
    for name, doc in documents.items():
        plan = expected_tree(case, owner=name) if doc.assembly else {"children": [], "total_occurrences": 0, "body_count": 1}
        doc.checks["header_state"] = check_headers(doc, plan["total_occurrences"], author["saved_files"][name])
        directory = header_directory(doc.header)
        refs = [typed(row["o"], "moReference_c") for row in doc.model["f68"]["list"]["items"]] if doc.assembly else []
        require(len(refs) == len(plan["children"]) and (doc.model["f1560"] == len(refs) if doc.assembly else not directory), "direct reference count differs")
        slots, ref_slots = map_bindings(doc, directory, refs)
        siblings = directory_checks(directory, refs, documents, slots)
        rows = occurrence_checks(doc, refs, directory, plan["children"], documents, states, slots, ref_slots)
        stamps = stamps_for(doc, refs, rows, states)
        state = {"refs": refs, "rows": rows, "stamp_pair": stamps, "leaves": [(doc.box, IDENTITY)]}
        states[name] = state
        doc.checks.update(f1300_own_geometry_stamp=doc.model["f1300"], cmgrhdr2_f50_geometry_stamp=stamps[0], cmgrhdr2_f4c_transform_stamp=stamps[1],
                          model_header_self_map_slot=slots[id(doc.header["f38"])])
        if not doc.assembly:
            continue
        require(not any(isinstance(root, Obj) and root.cls == "moReference_c" for root in doc.resolved_roots), "direct references unexpectedly recur as resolved roots")
        bounds, state["leaves"] = bounds_checks(doc, refs, rows, states)
        require(len(state["leaves"]) == plan["body_count"], "nested leaf expansion differs from the authored design")
        doc.checks.update(f1560_direct_occurrences=len(refs), resolved_root_count=len(doc.resolved_roots), direct_external_records=siblings,
                          refs=rows, cmgr=cmgr_checks(doc, refs, documents), bounds=bounds, xml=xml_checks(doc, documents, states))
    return {"source_author_sha256": AUTHORED[case["name"]], "original_reopen_sha256": DISCLOSED[case["name"]],
            "documents": {name: doc.checks for name, doc in documents.items()}}


def bind_replay(source, cases):
    directory = source.parents[1] / "NestedAssemblyReopen01" / "Inspection"
    path = checked(directory / "DisclosedNestedReopenResults.json", REPLAY_SHA, directory)
    data = json.loads(path.read_bytes())
    require(data["schema"] == REPLAY_SCHEMA and data["oracle_sha256"] == ORACLE and data["original_reopen_records"] == DISCLOSED and
            data["passed"] and data["read_only"] and data["controls_healthy"] and data["input_files_unchanged"] and
            data["distinct_processes"] == 4 and data["heldout_inputs_read"] == data["writer_output_count"] == 0, "disclosed native replay did not qualify")
    first, *rows, last = data["phases"]
    require([(row["mode"], row["name"], row["passed"], row["sha256"]) for row in (first, last)] ==
            [("control", label, True, CONTROL_SHA) for label in ("Before", "After")], "disclosed replay controls differ")
    for row, (name, case) in zip(rows, cases.items(), strict=True):
        require((row["name"], row["mode"], row["passed"], row["open_errors"], row["open_warnings"]) == (name, "reopen", True, 0, 0) and
                row["source_files_unchanged"] and {key: item["sha256"] for key, item in row["initial"]["definitions"].items()} ==
                {key: item["native_sha256"] for key, item in case["documents"].items()}, "disclosed replay measures a different artifact closure")
    return {"raw_result_sha256": REPLAY_SHA, "native_replay_sha256": data["replay_sha256"], "controls_healthy": True, "distinct_processes": 4}


def main():
    parser = argparse.ArgumentParser(description="Audit the exact two disclosed nested assembly source archives")
    parser.add_argument("source", type=Path)
    parser.add_argument("--bind-native-replay", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    inputs = source_cases(source)
    reg = registry()
    cases = {name: audit_case(case, paths, author, reg) for name, (case, paths, author) in inputs.items()}
    require(all(digest(path) == author["saved_files"][name]["sha256"] for _, paths, author in inputs.values() for name, path in paths.items()),
            "audit source bytes changed")
    replay = bind_replay(source, cases) if args.bind_native_replay else None
    result = {"schema": "kit.sw2026.disclosed-nested-assembly-archive-audit.v1", "tool_sha256": digest(SCRIPT), "version": VERSION,
              "typed_audit_passed": True, "heldout_payloads_read": 0, "writer_output_count": 0, "native_replay": replay, "cases": cases}
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
