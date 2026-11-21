from dataclasses import asdict, fields, replace
from hashlib import sha256

from OriginalPlanarNames import PLANES
from PlanarRegistryBuild import require
from para.concentric.ProveConcentricParentExploded import read_manager
from para.concentric.ProveConcentricParentLights import read_scene
from para.concentric.ProveConcentricParentNotes import read_notes

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import KAsmEarly, KAsmFolders, KAsmLate
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import NotesInput
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.TypedMates.ReadMateGroup import ReadMateGroup
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


MATES = "Contents/Config-0-MatesList"
KEYWORDS = "swXmlContents/KeyWords"
VISUALS = "ThirdPtyStore/VisualStates"
ROOT_CLASSES = (*KAsmEarly, "moDetailCabinet_c", *KAsmLate,
                *(("moRefPlane_c",) * 3), "moOriginProfileFeature_c", "moMateGroup_c")


def occurrences(model):
    owner = model.FieldsValue["f68"]
    listing = owner["list"]
    require(set(owner) == {"list", "tail"} and owner["tail"] == 0
            and set(listing) == {"n", "items"} and listing["n"] == len(listing["items"])
            and all(set(row) == {"o"} for row in listing["items"]),
            "source occurrence collection has unrepresented fields")
    return tuple(RequireNative(row["o"], "moReference_c") for row in listing["items"])


def owned_root(archive, *, present=True, link=None):
    link = ReadNativeLink(archive, 0) if link is None else link
    model = RequireNative(link.ConfigValue.RootValue, "moAssembly_c")
    roots = tuple(RequireNative(node) for node in link.ResolvedValue.RootsValue)
    require(tuple(node.ClassValue.NameValue for node in roots) == ROOT_CLASSES,
            "source resolved root classes or order differ from the supported planar system")
    environment, lights, light_inputs = read_scene(link, empty=not present)
    cabinet, notes, note_inputs = read_notes(link, 2 if present else 0)
    explosion = read_manager(link, present)
    require(all(not ReadChildren(node) for node in roots if node not in (environment, cabinet)),
            "source contains supplemental resolved root children")
    refs = occurrences(model)
    require(len(refs) in (2, 3), "source has an unsupported occurrence count")
    owners = {"resolved_root": roots, "environment_member": lights, "cabinet_member": notes,
              "exploded_manager": () if explosion is None else (explosion,), "occurrence_alias": refs}
    all_nodes = tuple(node for category in owners.values() for node in category)
    CheckTreeAlias(link, all_nodes)
    require(len({NativeNodeId(node) for node in all_nodes}) == len(all_nodes),
            "source root roles have duplicate persistent IDs")
    require(all(NativeNodeSpan(link, node)["stream"] == link.ConfigName for node in (*lights, *refs,
                *(() if explosion is None else (explosion,))))
            and all(NativeNodeSpan(link, node)["stream"] == link.StreamName for node in (cabinet, *notes, roots[-1])),
            "source model members are assigned to the wrong native stream")
    return link, model, owners, light_inputs, note_inputs


def root_system(owners, light_inputs, note_inputs):
    *folders, front, top, right, origin, group = owners["resolved_root"]
    cabinet = next(node for node in folders if node.ClassValue.NameValue == "moDetailCabinet_c")
    by_class = {node.ClassValue.NameValue: node for node in folders}
    lights = []
    for value in light_inputs:
        row = asdict(value)
        row.pop("CreatedValue")
        lights.append(row)
    return {
        "folders": [(role, ReadNativeName(by_class[role])) for role in KAsmFolders],
        "planes": [(axis, ReadNativeName(node)) for axis, node in zip("xyz", (right, top, front), strict=True)],
        "cabinet": ReadNativeName(cabinet), "origin": ReadNativeName(origin),
        "mate_group": ReadNativeName(group), "lights": lights,
        "notes": {"head": note_inputs.HeadName, "end": note_inputs.EndName} if note_inputs else None,
        "empty_exploded_view": bool(owners["exploded_manager"]),
    }


def archive_rows(owners):
    return {
        str(NativeNodeId(node)): {
            "id": NativeNodeId(node), "class": node.ClassValue.NameValue, "owner": role,
            "order_within_owner": index, "archive_index": node.IndexValue,
            "name": ReadNativeName(node) if node.FieldsValue.get("f18") is not None else None,
        }
        for role, rows in owners.items() for index, node in enumerate(rows)
    }


def keyword_rows(archive, owners, document=None):
    rows = archive_rows(owners)
    _, words = ParseKeywords(archive.require(KEYWORDS))
    features = tuple(row for row in words if row.xml_tag != "Configuration")
    require(len(features) == len(rows) and {str(row.object_id) for row in features} == set(rows),
            "assembly keyword inventory and typed root owners disagree")
    public = {} if document is None else {str(row.attributes["native_object_id"]): row
                                         for row in document.feature_timeline}
    if document is not None:
        require(len(public) == len(document.feature_timeline) == len(rows)
                and set(public) == set(rows),
                "normal feature identities differ from the actual keyword index")
    public_order = {identity: index for index, identity in enumerate(public)}
    result = []
    for word in features:
        identity = str(word.object_id)
        row = rows[identity]
        require(word.properties["Name"] == (row["name"] or "") and not word.dimensions,
                "assembly keyword name or content differs from its typed owner")
        if document is not None:
            actual = public[identity]
            reported_name = row["name"] or f"Exploded Views {identity}"
            require(dict(actual.attributes["native_properties"]) == word.properties and actual.name == reported_name,
                    "normal keyword row does not retain its native name owner")
        result.append({**row, "keyword_type": word.kind, "keyword_tag": word.xml_tag,
                       "public_order": public_order.get(identity)})
    return result


def ordered_group(source, portable, link, graph):
    original = source.assembly
    projected = portable.assembly
    require(source.metadata["solidworks.typed_mates_semantics"]["full_selected_mate_graph"]
            and len(original.mate_groups) == 1 and len(projected.mate_groups) == 1,
            "source or projected group lacks complete typed scope")
    (source_group,), (target_group,) = original.mate_groups, projected.mate_groups
    expected = ReadMateGroup(link, graph, original.mates, original.root_definition_id)
    require(source_group == expected and source_group.mate_ids == tuple(rule.id for rule in original.mates),
            "the ordinary source group differs from its actual ordered typed members")
    require(target_group.name == source_group.name and target_group.owner_definition_id == projected.root_definition_id
            and target_group.mate_ids == tuple(rule.id for rule in projected.mates),
            "the projected planar group changed its source membership or owner")
    occurrences_source = {row.id: row.order for row in original.instances}
    occurrences_projected = {row.id: row.order for row in projected.instances}
    source_child, = original.documents
    projected_child, = projected.documents
    source_planes = {row.id: row.name for row in source_child.document.support_planes}
    projected_planes = {row.id: row.name for row in projected_child.document.support_planes}

    def endpoint_signature(members, rules, poses, planes):
        by_id = {row.id: row for row in members}
        values = [by_id[key] for key in rules.entity_ids]
        return tuple((poses[row.instance_path[0]], planes[row.source_entity_id]) for row in values)

    membership = []
    for source_rule, destination_rule, node in zip(original.mates, projected.mates, graph.RootsValue, strict=True):
        first = endpoint_signature(original.mate_entities, source_rule, occurrences_source, source_planes)
        second = endpoint_signature(projected.mate_entities, destination_rule, occurrences_projected, projected_planes)
        require(first == second and (source_rule.name, source_rule.kind, source_rule.order, source_rule.alignment,
                    source_rule.suppressed, source_rule.driving, source_rule.value)
                == (destination_rule.name, destination_rule.kind, destination_rule.order, destination_rule.alignment,
                    destination_rule.suppressed, destination_rule.driving, destination_rule.value),
                "the projected mate changed scope order endpoints or driving intent")
        membership.append({"source_rule": source_rule.id, "projected_rule": destination_rule.id,
                           "source_native_id": NativeNodeId(node), "name": source_rule.name,
                           "class": node.ClassValue.NameValue, "ordered_endpoints": first})
    return {"source_group": source_group.id, "projected_group": target_group.id, "members": membership}


def project(source, portable, raw, source_system):
    require(sha256(raw).hexdigest() == source.source.sha256,
            "root presentation projection requires the actual physically decoded source")
    require(not any(key.startswith("kit.research_") for key in source.metadata),
            "research source status is outside the strict source projection")
    archive = SldprtArchive.from_bytes(raw)
    link, model, owners, lights, notes = owned_root(archive)
    system = root_system(owners, lights, notes)
    require(dict(system["folders"]) == source_system["folder_names"]
            and dict(system["planes"]) == source_system["planes"] == PLANES
            and (system["cabinet"], system["origin"], system["mate_group"])
            == (source_system["cabinet_name"], source_system["origin_name"], source_system["mate_group_name"]),
            "actual typed parent labels and principal role order disagree with the strict source")
    resolved_occurrences = tuple(ReadNativeName(node) for node in owners["occurrence_alias"])
    require(resolved_occurrences == tuple(row.name for row in source.assembly.instances)
            == tuple(row.name for row in portable.assembly.instances),
            "source or projected occurrence order differs from the actual config list")
    configuration, = source.configurations
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    active = manager.FieldsValue["f360"]
    native_config, = source.assembly.attributes["configurations"]
    root_name = ReadNativeName(model)
    require(active is manager.FieldsValue["f368"] and ReadNativeName(active) == configuration.name
            == portable.configurations[0].name and native_config["reference"] == root_name,
            "the strict configuration or its independent model-reference label differs")
    buffer = archive.require(MATES)
    payload, = source.brep_payloads
    graph = ReadMatesMut(buffer, link.ResolvedValue)
    encoded, _ = WriteMatesMut(graph.RootsValue, link.ResolvedValue)
    require(payload.format_id == "solidworks.mates" and str(payload.kind) == "mate-list"
            and str(payload.role) == "assembly_structure" and payload.data == encoded == buffer
            and payload.attributes["declared_count"] == len(payload.attributes["records"]) == len(graph.RootsValue),
            "the retained root mate payload has unrepresented records")
    membership = ordered_group(source, portable, link, graph)
    rows = keyword_rows(archive, owners, source)
    visuals = archive.require(VISUALS)
    states = source.assembly.attributes["display_states"]
    require(not any((source.sketches, source.selections, source.bodies, source.meshes, source.materials))
            and source.brep is None and not source.parameters
            and [diag.code for diag in source.diagnostics] == ["sldasm.native_record_unresolved"]
            and str(source.diagnostics[0].severity) == "info",
            "source root carries another model domain or diagnostic")
    return system, {
        "public_root_name": portable.metadata["name"], "native_model_name": root_name,
        "configuration": configuration.name, "native_config_reference": native_config["reference"],
        "root_owner_counts": {role: len(nodes) for role, nodes in owners.items()},
        "keyword_owner_rows": rows, "source_group": membership,
        "retained_mates": {"length": len(encoded), "sha256": sha256(encoded).hexdigest(), "typed_count": len(graph.RootsValue)},
        "source_clocks": {"lights": [asdict(item.CreatedValue) for item in lights],
                          "notes": [asdict(notes.HeadCreated), asdict(notes.EndCreated)] if notes else []},
        "source_diagnostics": [{"code": diag.code, "message": diag.message, "severity": str(diag.severity)}
                               for diag in source.diagnostics],
        "unconsumed_owner_domains": {
            "native_model_and_configuration_reference": root_name,
            "source_member_and_document_provenance": True,
            "source_assembly_attribute_names": sorted(source.assembly.attributes),
            "source_wrapper_metadata_names": sorted(source.metadata),
            "source_configuration_properties_bytes": len(archive.streams.get("docProps/Config-0-Properties.xml", b"")),
            "display_states": [{"name": row["name"],
                                "visibility": dict(row["native_attributes"])["swShowState"]} for row in states],
            "typed_display_owner_present": "typed_display_states" in source.assembly.attributes,
            "visual_states": {"stream": VISUALS, "bytes": len(visuals), "sha256": sha256(visuals).hexdigest()},
            "root_and_child_appearance_binding": "unrepresented",
        },
    }


def prepare_system(recipe, request, written_at):
    require(set(request) == {"folders", "planes", "cabinet", "origin", "mate_group", "lights", "notes", "empty_exploded_view"}
            and type(request["lights"]) is list and len(request["lights"]) == 4
            and type(request["notes"]) is dict and set(request["notes"]) == {"head", "end"}
            and request["empty_exploded_view"] is True and written_at == recipe.CreatedAt,
            "a planar source system request has unsupported members or an unowned event")
    keys = {field.name for field in fields(LightInput)} - {"CreatedValue"}
    lights = []
    for ordinal, member in enumerate(request["lights"], 1):
        require(type(member) is dict and set(member) == keys, "the light request has a nonsemantic field")
        direction = member["DirectionValue"]
        lights.append(LightInput(**{**member, "DirectionValue": tuple(direction) if direction is not None else None,
                                   "CreatedValue": FeatureInstant(written_at, ordinal)}))
    notes = NotesInput(request["notes"]["head"], request["notes"]["end"],
                       FeatureInstant(written_at, len(lights) + 1), FeatureInstant(written_at, len(lights) + 2))
    return replace(recipe, FolderNames=tuple(tuple(row) for row in request["folders"]),
                   PlaneNames=tuple(tuple(row) for row in request["planes"]),
                   CabinetName=request["cabinet"], OriginName=request["origin"], MateGroupName=request["mate_group"],
                   LightValues=tuple(lights), NotesValue=notes, HasEmptyExplodedView=True)
