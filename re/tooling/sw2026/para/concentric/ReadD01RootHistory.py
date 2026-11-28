from dataclasses import replace

from AuditConcentricDisplayState import ctext, file_signature
from ProjectD01Concentric import model_settings, require
from ProveD01ConcentricBridge import VISUAL, fingerprint
from ProveVisualStateStore import detached_context, owner_clocks, replay

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeywordName import AsmKeywordName
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import KAsmXmlRoles
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, ReadRows, RequireNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWriteCaps import KAsmWriteCaps
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


MATES = "Contents/Config-0-MatesList"
MANAGER = "Contents/CMgr"
HEADER = "Contents/Config-0-ModelHeader"
TOP = "Header2"


def rejection(call, expected):
    try:
        call()
    except ValueError as error:
        require(str(error) == expected, "unexpected source guard: " + str(error))
        return str(error)
    raise ValueError("unsupported root boundary was admitted")


def refusal_chain(document, root):
    inventory = replace(document, feature_timeline=(), brep_payloads=(), diagnostics=())
    provenance = replace(inventory, source=replace(document.source, attributes={}),
                         capabilities=document.capabilities & KAsmWriteCaps)
    metadata = replace(provenance, metadata={"name": root.name})
    graph = replace(metadata, assembly=replace(metadata.assembly, attributes={}))
    return {
        name: rejection(lambda: ReadAsmModel(value), expected)
        for name, value, expected in (
            ("original", document, "assembly root contains unprojected model content"),
            ("inventory_probe", inventory, "assembly has unsupported source extensions or capabilities"),
            ("provenance_probe", provenance, "assembly metadata has an unprojected field"),
            ("metadata_probe", metadata, "portable assembly graph is missing or extended"),
            ("graph_probe", graph, "configuration has unsupported inherited or extended state"),
        )
    }


def root_inventory(document, link, refs, archive):
    model, roots = link.ConfigValue.RootValue, link.ResolvedValue.RootsValue
    cabinet, = (row for row in roots if row.ClassValue.NameValue == "moDetailCabinet_c")
    categories = {
        "resolved": roots,
        "environment": ReadChildren(model.FieldsValue["f1e0"]),
        "annotations": ReadChildren(cabinet),
        "exploded": (model.FieldsValue["f1590"],),
        "occurrences": refs,
    }
    objects = {node.FieldsValue["f08"]: (role, node) for role, nodes in categories.items() for node in nodes}
    records = []
    for position, row in enumerate(document.feature_timeline):
        key = row.attributes["native_object_id"]
        role, node = objects[key]
        label = AsmKeywordName(node)
        if role == "exploded":
            require(label == "", "empty exploded manager cannot have a separate name")
            label = KAsmXmlRoles[node.ClassValue.NameValue][1] + " 1"
        require(row.order == position and row.name == label
                and row.provenance.native_id == str(key)
                and not (row.suppressed or row.selection_ids or row.parameter_ids
                         or row.input_feature_ids or row.configuration_states),
                "public root feature differs from its actual typed owner")
        records.append([key, position, role, row.name, node.ClassValue.NameValue])
    require(len(records) == len(objects) == sum(map(len, categories.values()))
            and {row[0] for row in records} == objects.keys(),
            "public root inventory does not bind all actual features")
    retained, = document.brep_payloads
    mate, = document.assembly.mates
    mate_payload = archive.require(MATES)
    mate_graph = ReadMatesMut(mate_payload, link.ResolvedValue)
    actual, = mate_graph.RootsValue
    require(retained.format_id == "solidworks.mates" and retained.kind == "mate-list"
            and retained.data == mate_payload and retained.sha256 == fingerprint(mate_payload)
            and retained.attributes["declared_count"] == len(retained.attributes["records"]) == 1
            and mate.attributes["native_payload_id"] == retained.id
            and mate.provenance.native_id == str(actual.FieldsValue["f08"])
            and actual.ClassValue.NameValue == "moMateConcentric" and mate.name == ReadNodeName(actual)
            and WriteMatesMut(mate_graph.RootsValue, link.ResolvedValue)[0] == mate_payload,
            "retained mate evidence differs from its exact typed assembly owner")
    diagnostic, = document.diagnostics
    require(diagnostic.code == "sldasm.native_record_unresolved" and diagnostic.severity == "info"
            and not any((document.sketches, document.selections, document.bodies, document.meshes, document.materials))
            and document.brep is None and document.DrawingValue is None,
            "source diagnostic or independent CAD inventory is outside the scoped root")
    return {"feature_count": len(records), "counts": {key: len(value) for key, value in categories.items()},
            "ordered_features": records, "retained_mate_sha256": retained.sha256,
            "retained_mate_bytes": len(mate_payload), "diagnostic": diagnostic.code,
            "excess_capabilities": sorted(map(str, document.capabilities - KAsmWriteCaps)),
            "source_attributes": sorted(document.source.attributes), "metadata": sorted(document.metadata)}


def file_identity(fields):
    return (file_signature(fields), ctext(fields["h10"]), ctext(fields["h18"]))


def handle_alias(a, b):
    return tuple(a[key] is b[key] for key in ("h10", "h18"))


def observed_contexts(config, store, refs):
    by_id = {row.FieldsValue["f08"]: row for row in refs}
    states = tuple(row["o"] for row in ReadRows(config.FieldsValue["fce8"]))
    require(len(states) == 3 and states[0].FieldsValue["f10"] is None,
            "source selected configuration has a foreign instance inventory")
    components = tuple(row["comp"] for row in store.head["root"].FieldsValue["comps"])
    actual = []
    for state, visual in zip(states[1:], components, strict=True):
        feature, context, chain, ext, file = detached_context(visual)
        ref = by_id[feature]
        conf_feature, conf_context, conf_chain, conf_ext, conf_file = detached_context(state.FieldsValue["f10"])
        live = RequireNode(ref.FieldsValue["f4f8"], "moExtFeature_c").FieldsValue
        require(feature == conf_feature == live["f44"] and live["f50"] is ref
                and ReadNodeName(ref) == ctext(ext["f38"]) == ctext(conf_ext["f38"]) == ctext(live["f38"])
                and state.FieldsValue["f28"] == ref.FieldsValue["f3c0"]
                and chain["f24"] == 1 and conf_chain["f24"] == 0
                and chain["f20"] == conf_chain["f20"] == 0
                and conf_ext["f50"] is ext["f50"] is None
                and context["owner"] is conf_context["owner"] is None
                and context["f48"] == conf_context["f48"] == file["f58"] == conf_file["f58"] == 0
                and context["f30"] == conf_context["f30"]
                and file["refcfg"] == {"f08": "", "f10": -1}
                and conf_file["refcfg"] == {"f08": ReadNodeName(config), "f10": config.FieldsValue["f08"]},
                "source context lost its actual occurrence or independent configuration selector")
        actual.append({
            "id": feature, "name": ReadNodeName(ref), "stamp": ref.FieldsValue["f3f0"],
            "context_stamp": context["f30"], "live": live["f10"],
            "visual_target": ext["f10"], "visual_context": file["shared"],
            "manager_target": conf_ext["f10"], "manager_context": conf_file["shared"],
        })
    require(tuple(row["id"] for row in actual) == tuple(by_id)[::-1],
            "source locator roles lost reverse registration order")
    return tuple(actual)


def snapshot(document, raw, reg):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    headers = link.ConfigValue.HeaderValue, ReadHeaderGraph(archive.require(TOP), 19000)
    require(all(WriteHeadGraph(node, 19000) == archive.require(stream)
                for stream, node in zip((HEADER, TOP), headers, strict=True)),
            "source headers fail their exact typed replay")
    files = tuple(RequireNode(node.FieldsValue["f38"], "moExtObject_c").FieldsValue["shared"] for node in headers)
    current = file_identity(files[0])
    require(file_identity(files[1]) == current and current[0][1] == 3
            and all(node.FieldsValue["f70"] == current[0][2] for node in headers)
            and ReadNodeName(link.ConfigValue.RootValue) == current[1],
            "source headers and modeled title do not own one actual assembly identity")
    manager = ReadCmgrMut(archive.require(MANAGER), 19000).RootValue
    config = manager.FieldsValue["f360"]
    only, = ReadRows(manager.FieldsValue["f370"]["items"])
    require(config is manager.FieldsValue["f368"] is only["o"] and manager.FieldsValue["f1f8"] == ""
            and ReadNodeName(config) == document.configurations[0].name == "Default"
            and WriteCmgrMut(manager, 19000) == archive.require(MANAGER),
            "source manager lacks the actual ordinary selected configuration")
    model = link.ConfigValue.RootValue.FieldsValue
    refs = tuple(row["o"] for row in ReadRows(model["f68"]["list"]["items"]))
    store, summary = replay(archive, reg)
    contexts = observed_contexts(config, store, refs)
    _, clocks = owner_clocks(archive, store)
    root = next(value for value in document.assembly.definitions if value.id == document.assembly.root_definition_id)
    _ = model_settings(link)
    return {
        "header_file": files[0], "contexts": contexts, "selected": [config.FieldsValue["f08"], ReadNodeName(config)],
        "header_presence": [h.FieldsValue["fec"] for h in headers], "plane_clocks": clocks,
        "inventory": root_inventory(document, link, refs, archive), "refusals": refusal_chain(document, root),
        "source_store": summary,
    }


def observe_transition(before, after):
    previous, current = (file_identity(row["header_file"]) for row in (before, after))
    require(not previous[2] and current[2] and previous[1] != current[1]
            and previous[0] == current[0]
            and before["selected"] == after["selected"] and before["plane_clocks"] == after["plane_clocks"]
            and before["inventory"]["ordered_features"] == after["inventory"]["ordered_features"],
            "source is outside the independently observed unlocated-to-first-locator history")
    roles = ("live", "visual_target", "visual_context", "manager_target", "manager_context")
    for phase, data in (("before", before), ("after", after)):
        chosen = previous if phase == "before" else current
        rows = data["contexts"]
        for row in rows:
            require(tuple(file_identity(row[role]) for role in roles)
                    == (chosen, chosen, previous, chosen, previous),
                    "source occurrence context no longer separates current target and former context")
            for target, context in (("visual_target", "visual_context"), ("manager_target", "manager_context")):
                require(handle_alias(row[target], row[context]) == (phase == "before",) * 2,
                        "source history did not preserve the real pooled or split handles")
        for target in roles:
            require(handle_alias(rows[0][target], rows[1][target]) == (True, True),
                    "source history has unrelated per-occurrence aliases")
    pairs = tuple(zip(before["contexts"], after["contexts"], strict=True))
    require(all(one["id"] == two["id"] and one["name"] == two["name"]
                and one["context_stamp"] == two["context_stamp"] == (101 + one["stamp"]) & 0xffffffff
                for one, two in pairs)
            and tuple(sorted(two["stamp"] - one["stamp"] for one, two in pairs)) == (0, 1),
            "source context clocks do not bind the actual prior/current occurrence states")
    return {"current_previous_signature": list(current[0]), "previous_model_name": previous[1],
            "current_model_name": current[1], "previous_locator_chars": len(previous[2]),
            "current_locator_chars": len(current[2]), "current_locator_sha256": fingerprint(current[2].encode()),
            "occurrence_clocks": [[one["id"], one["name"], one["stamp"], two["stamp"], two["context_stamp"]]
                                  for one, two in pairs], "separate_targets": 2}
