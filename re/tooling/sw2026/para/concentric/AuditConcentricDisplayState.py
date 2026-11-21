import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

import convert
from Classes import registry
from defs.Visual import load_visual_states, store_visual_states
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Assembly.Assembly import LocalName, XmlRoot
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, RequireNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import ReadMemberTime
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.api.ApiContext import KConvertEngine
from para.concentric.ProveConcentricSourceBrep import D01_LOCKED, RADIAL_LOCKED, checked, require


BASELINE = "5f730aea01ccfaaf05594e4acf8cddaf68ea0cc7"
INSTANCE = "swXmlContents/COMPINSTANCETREE"
VISUAL = "ThirdPtyStore/VisualStates"
KEYWORDS = "swXmlContents/KeyWords"
PUBLISHED_MANIFEST = "86729463bf5734f53e209de81f09976cc95bee8c7d33395eb512ec0ed8b823b3"
COMP_CLASS = "moContextChainComponent_c"
PLANE_CLASS = "moRefPlane_c"


def digest(data):
    return sha256(data).hexdigest()


def published_cases():
    base = REPO / "re/solidworks/v2026/corpus/assembly-synchronized"
    manifest = json.loads(checked(base / "Manifest.json", PUBLISHED_MANIFEST))
    require(manifest["heldout_payloads_read"] is False, "published controls must have disclosed provenance")
    rows = tuple(row for row in manifest["records"] if row["role"] == "parent")
    require(tuple(row["name"] for row in rows) == ("A12SyncedEmpty", "A13SyncedSingle", "A14SyncedRepeat"),
            "independent disclosed count-control closure changed")
    return tuple((row["name"], base / row["file"], row["sha256"], count, count > 0, True)
                 for count, row in enumerate(rows))


def children(node, name):
    return tuple(row for row in node if LocalName(row) == name)


def csv_field(value):
    fields = tuple(value.split(","))
    require(fields[-1] == "" and all(fields[:-1]), "display-state vector must be a counted trailing-comma sequence")
    return fields[:-1]


def xml_owner(root, model_refs, config_id, config_name, present):
    configuration_list, = children(root, "swConfigurationList")
    config, = children(configuration_list, "swConfiguration")
    require(config.attrib["swID"] == str(config_id) and config.attrib["swName"] == config_name,
            "actual XML config and selected binary config differ")
    model_list, = children(root, "swModelList")
    root_model, = (row for row in children(model_list, "swModel") if row.attrib["id"] == config.attrib["swModelRef"])
    occurrences = children(root_model, "swReference")
    ids = tuple(int(row.attrib["swID"]) for row in occurrences)
    require(ids == tuple(model_refs) and len(set(ids)) == len(ids), "XML references do not join actual live assembly occurrences")
    object_ids = tuple(int(row.attrib["id"]) for row in root.iter() if "id" in row.attrib)
    require(sorted(object_ids) == list(range(1, int(root.attrib["swObjCount"]) + 1)),
            "XML-local IDs or object count differ")
    lists = tuple(row for row in root.iter() if LocalName(row) == "swDisplayStateList")
    leaves = tuple(row for row in root.iter() if LocalName(row) == "swDisplayState")
    require((len(lists), len(leaves)) == ((1, 1) if present else (0, 0)),
            "component tree must have the selected display-list and state inventory")
    common = {"configuration": [int(config.attrib["id"]), config_id, config_name],
              "root_model_id": int(root_model.attrib["id"]), "xml_object_count": len(object_ids),
              "occurrences": [{
                  "xml_id": int(row.attrib["id"]), "feature_id": int(row.attrib["swID"]),
                  "name": row.attrib["swName"] + "-" + row.attrib["swReferenceNumber"],
                  "swHidden": row.attrib["swHidden"],
                  "swDisplayMode": int(row.attrib["swDisplayMode"]) if "swDisplayMode" in row.attrib else None,
                  "swHlrDisplayQuality": int(row.attrib["swHlrDisplayQuality"]) if "swHlrDisplayQuality" in row.attrib else None,
                  "swEdgesInShadedMode": row.attrib.get("swEdgesInShadedMode"),
              } for row in occurrences]}
    if not present:
        return common | {"state": None}
    listing, = lists
    state, = leaves
    require(children(config, "swDisplayStateList") == (listing,) and tuple(listing) == (state,) and not len(state),
            "display-state list or leaf is detached from the selected configuration")
    require(set(listing.attrib) == {"id", "swCompNameList"}
            and set(state.attrib) == {"id", "swDisplayStateName", "swShowState"},
            "unsupported component-tree state attributes")
    require((int(listing.attrib["id"]), int(state.attrib["id"])) == (len(object_ids) - 1, len(object_ids)),
            "display state and list IDs must follow the measured ordinary graph")
    membership = tuple(int(value) for value in csv_field(listing.attrib["swCompNameList"]))
    shows = csv_field(state.attrib["swShowState"])
    require(membership == ids and len(shows) == len(membership), "display vector does not bind ordered persistent occurrence IDs")
    require(all(value == "Yes" for value in shows), "display-state polarity is qualified only for the measured visible action")
    require(all(row["swHidden"] == "NO" for row in common["occurrences"]), "visible display-state action conflicts with occurrence hidden state")
    return common | {"state": {"list_id": int(listing.attrib["id"]), "id": int(state.attrib["id"]),
                                "name": state.attrib["swDisplayStateName"], "members": tuple(zip(membership, shows, strict=True))}}


def ctext(node):
    value = RequireNode(node, "moCStringHandle_c").FieldsValue
    text = value.get("f08", value.get("text"))
    require(type(text) is str, "canonical file handle must contain actual text")
    return text


def file_signature(shared):
    return (FieldInt(shared, "f08"), FieldInt(shared, "f20"), FieldInt(shared, "f28"))


def record_text(node):
    value = ctext(node)
    return {"codepoints": len(value), "sha256": digest(value.encode()), "span_bytes": node.EndOffset - node.StartOffset,
            "archive_slot": node.IndexValue, **({"value": value} if "\\" not in value and "/" not in value else {})}


def attrs_for(rows, holder, state_id, classes):
    require(len(rows) == holder == 1 and rows[0]["key"] == state_id and len(rows[0]["objs"]) == rows[0]["k"],
            "visual attributes do not bind the actual state key")
    objects = tuple(row["o"] for row in rows[0]["objs"])
    require(tuple(row.cls for row in objects) == classes and all(row.f["f08"] == state_id for row in objects),
            "visual attribute class or state ownership differs")
    return objects


def bind_visual(data, reg, source, config, index, model_refs, plane_rows, header):
    with reg.track_usage("load", VISUAL, sources=source.streams) as load:
        document, archive = load_visual_states(data, reg)
    with reg.track_usage("store", VISUAL) as store:
        again = store_visual_states(document, reg)
    require(again == data and not document.tail and load.completed and store.completed, "visual-state grammar lost stream coverage")
    usage = [value.snapshot() for value in (load, store)]
    require(all(not value["missing_schemas"] for value in usage), "visual-state audit reached an unknown schema")
    provisionals = sorted({name for value in usage for name in value["provisional_schemas"]})
    root = RequireNode(document.head["root"], "visStateKeyData_c")
    fields = root.f
    association, = fields["f118"]
    state, = fields["f0f0"]
    state_id = state["id"]
    require(document.head["file_version"] == 19000 and fields["n_ids"] == fields["n_states"] == 1
            and association == {"key": config, "value": state_id, "one": 1},
            "visual store state does not bind the actual persistent selected configuration")
    if index["state"] is not None:
        require(state["name"] == index["state"]["name"] and state_id != index["state"]["id"],
                "cache and XML share a state name in separate ID namespaces")
    require(fields["n_comps"] == len(fields["comps"]) == len(model_refs)
            and fields["n_ents"] == len(fields["f78"]) and fields["n_f88"] == len(fields["f88"]) == fields["n"] == len(fields["f08"]) == 0,
            "visual store has unclassified counts in the measured profile")
    header_file = RequireNode(header.FieldsValue["f38"], "moExtObject_c").FieldsValue["shared"]
    xml_refs = {row["feature_id"]: row for row in index["occurrences"]}
    modes = []
    locators = []
    for row in fields["comps"]:
        context = RequireNode(row["comp"], COMP_CLASS).FieldsValue
        chain = RequireNode(context["f20"], "moReferenceChain_c").FieldsValue
        entries = RequireNode(chain["f08"], "moExtFeatureList_c").FieldsValue
        own, = entries["f08"]
        ref = RequireNode(own["o"], "moExtFeature_c").FieldsValue
        persistent = FieldInt(ref, "f44")
        member = model_refs[persistent]
        public = xml_refs[persistent]
        require(chain["f24"] == entries["n"] == 1 and ref["f50"] is None and ctext(ref["f38"]) == ReadNodeName(member) == public["name"],
                "visual context chain fails direct occurrence ID and name ownership")
        live = RequireNode(member.FieldsValue["f4f8"], "moExtFeature_c").FieldsValue
        require(live["f50"] is member and live["f44"] == persistent, "binary model lacks its real direct occurrence owner")
        main = ref["f10"]
        context_file = RequireNode(context["f40"], "moExtObject_c").FieldsValue["shared"]
        require(file_signature(main) == file_signature(context_file) == file_signature(header_file)
                and all(ctext(main[key]) == ctext(header_file[key]) for key in ("h18", "h10")),
                "visual occurrence file signature or locator differs from the saved parent header")
        graphics, display, label = attrs_for(row["attrs"], row["m"], state_id, (
            "visStateVisualPropertiesAttribute_c", "visStateVisualStateAttribute_c", "visStateDisplayStateAttribute_c",
        ))
        numbers = tuple(FieldInt(display.f, key) for key in ("f10", "f14", "f18", "f1c"))
        require(numbers == (1, public["swDisplayMode"], int(public["swEdgesInShadedMode"] == "YES"), public["swHlrDisplayQuality"])
                and member.FieldsValue["hidden"] == 0 and graphics.f["f10"] is None and label.f["f18"] == state_id,
                "visual component display fields differ from the visible ordinary profile")
        modes.append({"feature_id": persistent, "visual_attribute": numbers, "internal_display_alias": label.f["f10"],
                      "alias_state_id": label.f["f18"], "chain_word": context["f30"]})
        locators.append((main, context_file))
    require(len({row["feature_id"] for row in modes}) == len(model_refs), "visual components duplicate a persistent occurrence")
    planes = []
    for row in fields["f78"]:
        handle = RequireNode(row["ref"], "moCompFeature_c").FieldsValue["ff0"]
        plane = RequireNode(plane_rows[handle["f00"]], PLANE_CLASS)
        clock = ReadMemberTime(plane).SecondsValue
        require(handle["f08"] == clock, "visual feature key does not bind the actual plane creation identity")
        graphics, display = attrs_for(row["attrs"], row["m"], state_id, (
            "visStateVisualPropertiesAttribute_c", "visStateVisualStateAttribute_c",
        ))
        require(graphics.f["f10"] is None, "visual plane has a populated appearance owner")
        planes.append({"feature_id": handle["f00"], "name": ReadNodeName(plane), "creation_seconds": clock,
                       "visual_attribute": tuple(display.f[key] for key in ("f10", "f14", "f18", "f1c"))})
    require(len({row["feature_id"] for row in planes}) == len(planes), "visual feature keys are duplicated")
    class_counts = Counter(row.EntryValue.ClassValue.NameValue for row in archive.map_state().state.EntriesValue
                           if isinstance(row.EntryValue, ArchiveNode))
    info = {"bytes": len(data), "sha256": digest(data), "byte_identity": True, "unread_tail_bytes": 0,
            "map_counter": archive.count, "object_classes": dict(class_counts), "file_version": document.head["file_version"],
            "shown_header_word": document.head["shown"], "state_header_words": [fields["f15c"], fields["f158"]],
            "config_to_state": association, "state": state, "components_in_store_order": modes, "feature_plane_rows": planes,
            "provisional_schemas": provisionals, "strict_schema_admitted": not provisionals}
    return root, locators, info


def compare_typed(left, right):
    values = {}
    seen = set()
    alias_targets = {}

    def visit(a, b, path):
        if isinstance(a, ArchiveNode) and isinstance(b, ArchiveNode):
            require(a.ClassValue == b.ClassValue, "depth-edit visual graph changed an owner schema")
            alias_targets.setdefault(a, set()).add(b)
            if (a, b) not in seen:
                seen.add((a, b))
                visit(a.FieldsValue, b.FieldsValue, path + (a.ClassValue.NameValue,))
        elif isinstance(a, dict) and isinstance(b, dict):
            require(a.keys() == b.keys(), "depth-edit visual graph changed its fields")
            for key in a:
                visit(a[key], b[key], path + (key,))
        elif isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
            require(len(a) == len(b), "depth-edit visual graph changed a sequence count")
            for i, (first, second) in enumerate(zip(a, b, strict=True)):
                visit(first, second, path + (str(i),))
        elif a != b:
            values["/".join(path)] = [a, b]

    visit(left, right, ())
    return values, {node: targets for node, targets in alias_targets.items() if len(targets) != 1}


def edit_delta(original, edited):
    old, old_locators, old_info = original
    new, new_locators, new_info = edited
    changes, aliases = compare_typed(old, new)
    old_main, old_context = old_locators[0]
    new_main, new_context = new_locators[0]
    require({path.split("/")[-3] for path in changes} == {"h18", "h10"} and len(changes) == 2
            and all("/moExtFeature_c/f10/" in path for path in changes),
            "edit varies visual state outside its two actual parent locator fields")
    require({node for node in aliases} == {old_main["h18"], old_main["h10"]}, "unexpected visual cache alias split")
    rows = []
    for field in ("h18", "h10"):
        require(old_main[field] is old_context[field] and new_main[field] is not new_context[field]
                and aliases[old_main[field]] == {new_main[field], new_context[field]}
                and ctext(old_context[field]) == ctext(new_context[field]),
                "old context file handle does not survive separately after Save As")
        before = record_text(old_main[field])
        after = record_text(new_main[field])
        preserved = record_text(new_context[field])
        old_ref_width = len(EncodeTag(ArchiveTag("ObjectRef", old_context[field].IndexValue)))
        rows.append({"field": field, "source_main_and_context": before, "edited_main": after, "preserved_context": preserved,
                     "parent_owner_byte_growth": after["span_bytes"] - before["span_bytes"],
                     "context_alias_split_byte_growth": preserved["span_bytes"] - old_ref_width})
    actual = new_info["bytes"] - old_info["bytes"]
    require(actual == sum(row["parent_owner_byte_growth"] + row["context_alias_split_byte_growth"] for row in rows),
            "file handle wire framing does not explain every visual-state byte of size delta")
    classes = {key: new_info["object_classes"][key] - old_info["object_classes"][key] for key in old_info["object_classes"]}
    require({name: value for name, value in classes.items() if value} == {"moCStringHandle_c": 2},
            "visual cache changed an additional object class")
    return {"bytes_added": actual, "map_counter_delta": new_info["map_counter"] - old_info["map_counter"],
            "changed_typed_paths": sorted(changes), "alias_splits": rows, "added_object_classes": {"moCStringHandle_c": 2}}


def model_inputs(archive):
    link = ReadNativeLink(archive, 0)
    model = RequireNode(link.ConfigValue.RootValue, "moAssembly_c").FieldsValue
    items = model["f68"]["list"]["items"] if model["has_list68"] else []
    references = tuple(RequireNode(item["o"], "moReference_c") for item in items)
    refs = {FieldInt(row.FieldsValue, "f08"): row for row in references}
    require(len(refs) == len(references), "binary references contain a repeated feature ID")
    config = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue.FieldsValue
    active = RequireNode(config["f360"], "moConfiguration_c")
    require(config["f368"] is active, "configuration manager lacks its actual selected alias")
    planes = {FieldInt(row.FieldsValue, "f08"): row
              for row in link.ResolvedValue.RootsValue if row.ClassValue.NameValue == PLANE_CLASS}
    return refs, FieldInt(active.FieldsValue, "f08"), ReadNodeName(active), planes, link.ConfigValue.HeaderValue


def public_projection(document, index):
    values = document.assembly.attributes["display_states"]
    instances = {row.attributes["native_feature_id"]: row for row in document.assembly.instances}
    require(len(instances) == len(index["occurrences"]), "normal reader changes the occurrence inventory")
    for entry in index["occurrences"]:
        row = instances[entry["feature_id"]]
        require(row.provenance.native_id == str(entry["xml_id"]) and row.hidden is (entry["swHidden"] == "YES")
                and row.name == entry["name"], "normal reader lost direct occurrence identity or hidden polarity")
    if index["state"] is None:
        require(not values, "normal reader invented a display-state leaf")
        return None
    state = index["state"]
    display, = values
    raw = dict(display["native_attributes"])
    require(display["native_object_id"] == state["id"] and display["name"] == state["name"]
            and display["configuration_id"] is None and set(raw) == {"id", "swDisplayStateName", "swShowState"}
            and "swCompNameList" not in raw, "existing public display projection no longer fits the measured leaf-only contract")
    return {"leaf_id": display["native_object_id"], "name": display["name"], "config_id": None,
            "preserved_leaf_attribute_names": sorted(raw), "stores_owning_list": False}


def scope_errors(tree, refs, config, name):
    actions = {"xml_id_substitution": ("list", "swCompNameList", "4,7,"),
               "duplicate_occurrence": ("list", "swCompNameList", "24,24,"),
               "short_show_vector": ("state", "swShowState", "Yes,"),
               "unmeasured_mixed_polarity": ("state", "swShowState", "Yes,No,"),
               "unmapped_binary_config": ("config", "swID", "1")}
    results = {}
    for test, (role, key, value) in actions.items():
        copy = deepcopy(tree)
        cfg, = children(children(copy, "swConfigurationList")[0], "swConfiguration")
        listing, = children(cfg, "swDisplayStateList")
        display, = children(listing, "swDisplayState")
        {"list": listing, "state": display, "config": cfg}[role].set(key, value)
        try:
            xml_owner(copy, refs, config, name, True)
        except ValueError as error:
            results[test] = str(error)
        else:
            raise ValueError("unsupported display-state mutation admitted: " + test)
    return results


def main():
    parser = argparse.ArgumentParser(description="Audit disclosed assembly display state and VisualStates ownership")
    parser.add_argument("disclosed_root", type=Path)
    parser.add_argument("new_receipt", type=Path)
    args = parser.parse_args()
    require(Path(convert.__file__).resolve().is_relative_to((REPO / "src").resolve()), "observer imports the wrong SDK closure")
    root = args.disclosed_root.resolve()
    d01 = root / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(d01 / "lock.json", "bdd8bf3782ccf01991a3ac402da2923f2d320728792fb8ccb500f73189e9f90b"))
    require(lock["source_locked"] and not lock["heldout_source_locked"], "only the disclosed D01 closure is admitted")
    paths = tuple(("D01" + role, d01 / "Native" / role / "ConcentricD01AlignedFree.SLDASM", value[0], 2, True, True)
                  for role, value in D01_LOCKED.items()) + tuple(
        ("Radial" + role, root / "RadialConcentric01" / role / "RadialConcentricProbe.SLDASM", value[0], 2,
         role == "Working", role == "Working") for role, value in RADIAL_LOCKED.items()) + published_cases()
    values = {}
    visual = {}
    refusals = {}
    reg = registry()
    for label, source, sha, count, xml_state, visual_store in paths:
        payload = checked(source, sha)
        archive = SldprtArchive.from_bytes(payload)
        refs, config, name, planes, header = model_inputs(archive)
        require(len(refs) == count, "disclosed native occurrence count differs")
        tree = XmlRoot(archive.require(INSTANCE))
        index = xml_owner(tree, refs, config, name, xml_state)
        doc = KConvertEngine.read(source, options=ReadOptions(
            strict=True, include_brep=False, include_tessellation=False, values={"resolve_components": False}))
        require(doc.source.sha256 == sha and not doc.assembly.documents, "normal reader changed the pinned parent or loaded children")
        neutral = public_projection(doc, index)
        cache = archive.get(VISUAL)
        require((cache is not None) == visual_store, "third-party store presence differs")
        if cache is not None:
            visual[label] = bind_visual(cache, reg, archive, config, index, refs, planes, header)
        _, keywords = ParseKeywords(archive.require(KEYWORDS))
        require(not any(row.kind in ("DisplayState", "Display State")
                        or (index["state"] is not None and row.name == index["state"]["name"]) for row in keywords),
                "unexpected independent KeyWords display-state owner")
        values[label] = {"native_sha256": sha, "component_tree_sha256": digest(archive.require(INSTANCE)),
                         "xml": index, "public": neutral, "visual": visual[label][2] if label in visual else None}
        if label == "D01Source":
            refusals = scope_errors(tree, refs, config, name)
    require(values["D01Source"]["xml"] == values["D01Edited"]["xml"],
            "D01 depth-edit save changed the supported display-state owner")
    delta = edit_delta(visual["D01Source"], visual["D01Edited"])
    for _, path, sha, _, _, _ in paths:
        checked(path, sha)
    sources = ("src/convert/adapters/solidworks/Assembly/Assembly.py", "src/convert/adapters/solidworks/Core/Adapter.py",
               "re/tooling/sw2026/serial/defs/Visual.py", "re/tooling/sw2026/serial/defs/VisualRefs.py",
               "re/tooling/sw2026/para/concentric/AuditConcentricDisplayState.py")
    report = {"schema": "kit.sw2026.disclosed-concentric-display-state.v1", "baseline": BASELINE,
              "source_hashes": {path: digest((REPO / path).read_bytes()) for path in sources},
              "cases": values, "d01_visual_edit_save_delta": delta, "bounded_projection_refusals": refusals,
              "conclusions": {"observed_xml_show_token": "Yes", "mixed_visibility_proven": False,
                              "native_stream_precedence_proven": False, "visual_store_omission_qualified": False},
              "native_processes": 0, "heldout_inputs_read": 0, "writer_outputs": 0, "passed": True}
    with args.new_receipt.open("x") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
