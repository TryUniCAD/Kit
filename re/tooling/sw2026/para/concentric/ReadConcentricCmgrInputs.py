from dataclasses import asdict, dataclass
from pathlib import PureWindowsPath

from AuditConcentricDisplayState import compare_typed, ctext
from ProjectD01Concentric import require
from ProveD01ConcentricBridge import VISUAL, fingerprint
from ProveVisualStateStore import detached_context
from ReadD01RootHistory import file_identity
from defs.Visual import load_visual_states

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, ReadRows, RequireNode
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


CMGR = "Contents/CMgr"
MANAGER_HEADER = "Contents/CMgrHdr2"
HAS_CHILD_VIEW = 0x100000


@dataclass(frozen=True, slots=True)
class ChildViewIntent:
    occurrence_id: str
    configuration_name: str
    display_name: str


def config_owner(archive, kind):
    manager = ReadCmgrMut(archive.require(CMGR), 19000).RootValue
    f = manager.FieldsValue
    selected, = ReadRows(f["f370"]["items"])
    actual = RequireNode(f["f360"], kind)
    require(actual is f["f368"] is selected["o"] and f["f370"]["n"] == 1
            and f["f1f8"] == "" and WriteCmgrMut(manager, 19000) == archive.require(CMGR),
            "manager requires its actual ordinary selected configuration and exact typed body")
    return actual


def child_display(store, config, reg):
    contents = store.require(VISUAL)
    with reg.track_usage("load", VISUAL, sources=store.streams) as tracking:
        document, _ = load_visual_states(contents, reg)
    summary = tracking.snapshot()
    root = RequireNode(document.head["root"], "visStateKeyData_c").FieldsValue
    selected, = root["f118"]
    state, = root["f0f0"]
    require(document.head["file_version"] == 19000 and not document.tail
            and summary["completed"] and not any(summary[key] for key in (
                "raw_operations", "missing_schemas", "provisional_schemas"))
            and selected == {"key": config.FieldsValue["f08"], "value": state["id"], "one": 1}
            and type(state["id"]) is int and state["id"] >= 1
            and state["name"] == "<Default>_Display State 1",
            "child appearance requires the actual default state of its selected configuration")
    return ReadNodeName(config), state["name"], state["id"]


def contextual_rows(config):
    states = tuple(row["o"] for row in ReadRows(config.FieldsValue["fce8"]))
    require(len(states) == 3 and states[0].FieldsValue["f10"] is None
            and states[0].FieldsValue["f28"] == {"f08": "", "f10": -1}
            and not states[0].FieldsValue["f18"] & HAS_CHILD_VIEW,
            "assembly manager requires its actual self row and two independently registered occurrences")
    for row in states[1:]:
        fields = RequireNode(row, "moConfigObject_c").FieldsValue
        feature, context, chain, target, file = detached_context(fields["f10"])
        require(chain["f24"] == chain["f20"] == 0 and target["f50"] is None
                and context["owner"] is None and context["f48"] == 0 and file["f58"] == 0
                and file["refcfg"] == {"f08": ReadNodeName(config), "f10": config.FieldsValue["f08"]},
                "CMgr detached context lost its actual parent configuration")
        yield feature, fields, context, target, file


def manager_root_stamps(archive, root, config, refs):
    manager = ReadMgrHeader(archive.require(MANAGER_HEADER), 19000).RootValue
    row, = ReadRows(manager.FieldsValue["f08"]["items"])
    actual = RequireNode(row["o"], "dmConfigHeader_c").FieldsValue
    poses = tuple(ref.FieldsValue["f3f0"] for ref in refs)
    require(all(101 < stamp <= 0xffffffff for stamp in poses) and len(refs) == 2,
            "saved root requires actual initialized direct placement stamps")
    transform = sum(poses) & 0xffffffff
    geometry = (root.FieldsValue["f1300"] + sum(ref.FieldsValue["f3f4"] for ref in refs)) & 0xffffffff
    require((actual["f30"], actual["f10"], actual["f38"])
            == (config.FieldsValue["f08"], ReadNodeName(config), config.FieldsValue["f860"])
            and (actual["f4c"], actual["f50"]) == (transform, geometry)
            and WriteMgrHeader(manager, 19000)[0] == archive.require(MANAGER_HEADER),
            "manager header aggregate stamp or configuration differs from its actual saved root")
    return transform, geometry


def child_directory(link, headers, child_archive, child_link, refs):
    root = child_link.ConfigValue.RootValue
    child = child_link.ConfigValue.HeaderValue
    child_file = RequireNode(child.FieldsValue["f38"], "moExtObject_c")
    directory = RequireNode(refs[0].FieldsValue["f3b0"], "moExtObject_c")
    shared = directory.FieldsValue
    managed = ReadMgrHeader(child_archive.require(MANAGER_HEADER), 19000).RootValue
    expected = ReadFileKey(child_file)
    directory_state = tuple(shared[key] for key in ("f48", "f60", "f70", "f78"))
    for head in headers:
        header_list = RequireNode(head.FieldsValue["f30"], "moExtObjectList_c")
        (row,) = header_list.FieldsValue["items"]
        value = RequireNode(row, "moExtObject_c")
        require(ReadFileKey(value) == expected
                and tuple(value.FieldsValue[key] for key in ("f48", "f60", "f70", "f78")) == directory_state,
                "both directory headers must identify the actual child creation and current save")
    require(refs == tuple(row["o"] for row in ReadRows(link.ConfigValue.RootValue.FieldsValue["f68"]["list"]["items"]))
            and all(row.FieldsValue["f3b0"] is directory for row in refs)
            and tuple(link.ConfigValue.HeaderValue.FieldsValue["f30"].FieldsValue["items"]) == (directory,)
            and ReadFileKey(directory) == expected and expected[2] == 2
            and expected[3] == child.FieldsValue["f70"]
            and shared["f60"] == child_file.FieldsValue["f60"]
            and shared["f70"] == managed.FieldsValue["f60"]
            and shared["f48"] == len(refs) and shared["f78"] == 0
            and WriteMgrHeader(managed, 19000)[0] == child_archive.require(MANAGER_HEADER),
            "occurrences are detached from the actual saved child directory, creation or manager")
    return directory, (
        child.FieldsValue["f40"], child.FieldsValue["f48"], root.FieldsValue["f1300"], expected[3],
    )


def owned_source(document, archive, child_archive, child_digest, reg, mapping):
    parent_link = ReadNativeLink(archive, 0)
    child_link = ReadNativeLink(child_archive, 0)
    header = parent_link.ConfigValue.HeaderValue
    header_file = header.FieldsValue["f38"].FieldsValue["shared"]
    parent_config = config_owner(archive, "moConfiguration_c")
    child_config = config_owner(child_archive, "moPartConfiguration_c")
    display = child_display(child_archive, child_config, reg)
    root = parent_link.ConfigValue.RootValue
    refs = tuple(row["o"] for row in ReadRows(root.FieldsValue["f68"]["list"]["items"]))
    require(len(refs) == 2 and len({row.FieldsValue["f08"] for row in refs}) == 2
            and file_identity(header_file)[0][2] == header.FieldsValue["f70"],
            "source parent requires exactly two real references and its own creation identity")
    active = ReadHeaderGraph(archive.require("Header2"), 19000)
    top_file = RequireNode(active.FieldsValue["f38"], "moExtObject_c").FieldsValue["shared"]
    require(file_identity(top_file) == file_identity(header_file)
            and active.FieldsValue["f70"] == header.FieldsValue["f70"]
            and ReadNodeName(root) == file_identity(header_file)[1],
            "both parent headers must identify the actual document title and creation owner")
    directory, expected_stamp = child_directory(parent_link, (header, active), child_archive, child_link, refs)
    root_stamps = manager_root_stamps(archive, root, parent_config, refs)
    graph = document.assembly
    root_def, = [row for row in graph.definitions if row.id == graph.root_definition_id]
    child_def, = [row for row in graph.definitions if row is not root_def]
    child_doc, = graph.documents
    require(root_def.configuration_name == ReadNodeName(parent_config)
            and child_def.document_id == child_doc.id and child_def.configuration_name == display[0]
            and child_doc.document.source.sha256 == child_digest
            and PureWindowsPath(ReadFileKey(directory)[1]).stem == child_def.name,
            "source document definitions do not resolve the selected archive configuration and file")
    public = {row.attributes["native_feature_id"]: row for row in graph.instances}
    intent = []
    rows = []
    for (feature, row, context, target, file), ref in zip(contextual_rows(parent_config), refs[::-1], strict=True):
        ref_fields = ref.FieldsValue
        live = ref_fields["f4f8"].FieldsValue
        occurrence = public[feature]
        options = RequireNode(row["f08"], "moConfig_c")
        defaults = RequireNode(parent_config.FieldsValue["fc50"], "moConfig_c")
        changes, aliases = compare_typed(options, defaults)
        require(not aliases and set(changes) == {"moConfig_c/f48", "moConfig_c/f50", "moConfig_c/f64"}
                and (options.FieldsValue["f48"], options.FieldsValue["f50"]) == display[1:]
                and (defaults.FieldsValue["f48"], defaults.FieldsValue["f50"]) == ("", -1)
                and changes["moConfig_c/f64"] == [0, -1] and row["f18"] == 0x111 | HAS_CHILD_VIEW
                and ref_fields["f08"] == feature == live["f44"] and live["f50"] is ref
                and ctext(target["f38"]) == ctext(live["f38"]) == ReadNodeName(ref) == occurrence.name
                and file_identity(target["f10"]) == file_identity(live["f10"]) == file_identity(header_file)
                and file_identity(file["shared"])[0] == file_identity(header_file)[0]
                and row["f28"] == ref_fields["f3c0"] == {"f08": display[0], "f10": child_config.FieldsValue["f08"]}
                and occurrence.owner_definition_id == root_def.id and occurrence.definition_id == child_def.id
                and occurrence.configuration_name == display[0]
                and tuple(ref_fields[key] for key in ("f3e0", "f3e8", "f3f4")) == expected_stamp[:3]
                and ref_fields["f3f8"] == 101,
                "saved occurrence does not select the actual child display and current owned part")
        neutral_id = mapping[occurrence.id]
        intent.append(asdict(ChildViewIntent(neutral_id, display[0], display[1])))
        rows.append({"feature_id": feature, "neutral_occurrence": neutral_id, "current_placement_stamp": ref_fields["f3f0"],
                     "context_stamp": context["f30"], "actual_child_view": list(display[1:])})
    mate, = graph.mates
    return tuple(intent), {
        "rows_in_registration_order": rows, "source_parent_creation": header.FieldsValue["f70"],
        "source_child_creation": expected_stamp[-1], "child_update_time_and_geometry": expected_stamp[:3],
        "parent_manager_sha256": fingerprint(archive.require(CMGR)),
        "current_manager_transform_and_geometry": root_stamps,
        "child_file_role": [child_def.name, child_def.configuration_name],
        "alignment": str(mate.alignment), "rotation_locked": mate.attributes["rotation_locked"],
        "mate_entity_order": list(mate.entity_ids),
    }
