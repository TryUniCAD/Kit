from collections import Counter

from PlanarRegistryBuild import require
from para.concentric.AuditConcentricDisplayState import attrs_for, compare_typed, ctext, file_signature, model_inputs
from para.concentric.ProveVisualStateStore import replay

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


DISPLAY = "<Default>_Display State 1"
PROPERTY = "visStateVisualPropertiesAttribute_c"
STATE = "visStateVisualStateAttribute_c"
LABEL = "visStateDisplayStateAttribute_c"
RENDERER_REFUSAL = "SOLIDWORKS part Definition has an alternate renderer profile"
COMPOUND = Counter(dict.fromkeys(("moContextChainComponent_c", "moReferenceChain_c",
                                "moExtFeatureList_c", "moExtFeature_c", "moCStringHandle_c", "moExtObject_c"), 1))


def node(value, name):
    require(isinstance(value, ArchiveNode) and value.ClassValue.NameValue == name,
            "visual graph reached a different typed owner: " + name)
    return value.FieldsValue


def order_keys(archive):
    link = ReadNativeLink(archive, 0)
    top = ReadHeaderGraph(archive.require("Header2"), 19000)
    return link, (link.ConfigValue.HeaderValue, top)


def flags(value):
    return [value.FieldsValue[key] for key in ("f10", "f14", "f18", "f1c")]


def key_data(document, configuration, name):
    values = node(document.head["root"], "visStateKeyData_c")
    require(document.head["file_version"] == 19000 and document.head["shown"] == 0
            and (values["f15c"], values["f158"], values["n_f88"], values["n"]) == (5, 0, 0, 0)
            and values["f118"] == [{"key": configuration, "value": 1, "one": 1}]
            and values["f0f0"] == [{"id": 1, "name": name, "f384": 0, "f394": 0, "f38c": 0}],
            "visual graph lost its single actual configuration and state")
    return values


def refs_for(rows, headers, features):
    references, properties, states, units = [], [], [], []
    for row in rows:
        ref = node(row["ref"], "moCompFeature_c")
        prop, state = attrs_for(row["attrs"], row["m"], 1, (PROPERTY, STATE))
        feature_id = ref["ff0"]["f00"]
        feature = features[feature_id]
        time = ref["ff0"]["f08"]
        require(all(DatumTime(header, feature_id) == time for header in headers)
                and node(ref["f58"], "moUnitComponent_c") == {"owner": None, "has_ext": 0}
                and prop.FieldsValue["f10"] is None,
                "visual feature lost its independent detached unit or actual creation owner")
        references.append([feature_id, ReadNodeName(feature), time, flags(state)])
        properties.append(prop)
        states.append(state)
        units.append(ref["f58"])
    require(len(set(units)) == len(units) and len(set(properties)) == 1
            and len({row[0] for row in references}) == len(rows),
            "visual features do not retain separate references and one shared absent appearance")
    return references, properties[0], states, units


def parent_store(archive, registry):
    document, info = replay(archive, registry)
    _, headers = order_keys(archive)
    refs, config, _, planes, header = model_inputs(archive)
    header_file = node(header.FieldsValue["f38"], "moExtObject_c")["shared"]
    values = key_data(document, config, "Display State-1")
    require(values["n_ents"] == len(planes) == 3 and values["n_comps"] == len(refs),
            "parent visibility cardinality differs from the actual assembly")
    actual, targets, locators, props, states, labels = [], [], [], [], [], []
    objects = Counter()
    compound_slots = set()
    for row in values["comps"]:
        context = node(row["comp"], "moContextChainComponent_c")
        chain = node(context["f20"], "moReferenceChain_c")
        group = node(chain["f08"], "moExtFeatureList_c")
        entry, = group["f08"]
        target = node(entry["o"], "moExtFeature_c")
        file = node(context["f40"], "moExtObject_c")
        key = target["f44"]
        live = refs[key]
        prop, state, label = attrs_for(row["attrs"], row["m"], 1, (PROPERTY, STATE, LABEL))
        require(context["owner"] is None and context["f48"] == 0
                and context["f30"] == (101 + live.FieldsValue["f3f0"]) & 0xFFFFFFFF
                and chain["f24"] == group["n"] == 1
                and target["f50"] is None and ctext(target["f38"]) == ReadNodeName(live)
                and live.FieldsValue["f4f8"].FieldsValue["f50"] is live
                and file_signature(target["f10"]) == file_signature(file["shared"]) == file_signature(header_file)
                and all(target["f10"][field] is file["shared"][field] for field in ("h10", "h18"))
                and prop.FieldsValue["f10"] is None
                and flags(state) == [1, 6, 0, 1]
                and label.FieldsValue == {"f08": 1, "f10": DISPLAY, "f18": 1},
                "compound occurrence loses its live identity, order word, pooled file or visibility")
        components = (row["comp"], context["f20"], chain["f08"], entry["o"], target["f38"], context["f40"])
        slots = [value.IndexValue for value in components]
        require(all(type(slot) is int and slot > 0 for slot in slots)
                and len(set(slots)) == 6 and compound_slots.isdisjoint(slots),
                "an occurrence must own six independently allocated compound entries")
        objects.update(value.ClassValue.NameValue for value in components)
        compound_slots.update(slots)
        actual.append([key, ReadNodeName(live), context["f30"], slots])
        targets.append(target["f38"])
        locators.append(tuple(file["shared"][field] for field in ("h10", "h18")))
        props.append(prop)
        states.append(state)
        labels.append(label)
    ordered = tuple(refs)
    require(tuple(row[0] for row in actual) == ordered[::-1]
            and len(set(targets)) == len(refs) and len({tuple(pair) for pair in locators}) == 1
            and len(set(props)) == len(set(states)) == len(set(labels)) == 1
            and objects == Counter({key: count * len(refs) for key, count in COMPOUND.items()}),
            "compound occurrences do not follow actual reverse allocation and shared state aliases")
    plane_refs, plane_prop, plane_states, _ = refs_for(values["f78"], headers, planes)
    require([row[0] for row in plane_refs] == list(planes)[::-1]
            and all(row[-1] == [0, 6, 1, 0] for row in plane_refs)
            and props[0] is plane_prop and len(set(plane_states)) == 1 and plane_states[0] is not states[0],
            "parent plane owner order or actual shared property association differs")
    return {**info, "occurrence_rows_in_wire_order": actual, "compound_objects": dict(objects),
            "configuration_id": config, "parent_header_locator_codepoints": len(ctext(header_file["h18"])),
            "parent_header_model": ctext(header_file["h10"]), "plane_keys": plane_refs}


def child_store(archive, registry, *, rich):
    document, info = replay(archive, registry)
    link, headers = order_keys(archive)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue.FieldsValue
    config = manager["f360"]
    require(config is manager["f368"] and ReadNodeName(config) == "Default", "child selected configuration is ambiguous")
    values = key_data(document, config.FieldsValue["f08"], DISPLAY)
    require(values["n_ents"] == 6 and values["n_comps"] == 0, "child self visibility must own six actual entities")
    holder, *rows = values["f78"]
    base = node(holder["ref"], "moCompHolder_c")
    prop, state = attrs_for(holder["attrs"], holder["m"], 1, (PROPERTY, STATE))
    features = {row.FieldsValue["f08"]: row for row in link.ResolvedValue.RootsValue
                if isinstance(row, ArchiveNode) and "f08" in row.FieldsValue}
    keys, other_property, states, units = refs_for(rows, headers, features)
    require([row[1] for row in keys[1:]] == ["Origin", "Right Plane", "Top Plane", "Front Plane"]
            and features[keys[0][0]].ClassValue.NameValue == "moProfileFeature_c"
            and node(base["f58"], "moUnitComponent_c") == {"owner": None, "has_ext": 0}
            and base["f58"] not in units and prop is not other_property
            and states[0] is states[1] is state and flags(state) == [1, 6, 1, 0]
            and states[2] is states[3] is states[4] and states[2] is not state
            and flags(states[2]) == [0, 6, 1, 0],
            "child holder, sketch/origin or plane appearance association differs")
    looks = (link.ConfigValue.RootValue.FieldsValue["f78"], config.FieldsValue["f78"], prop.FieldsValue["f10"])
    roles = {}
    for role, appearance in zip(("model", "configuration", "holder"), looks, strict=True):
        fields = node(appearance, "moVisualProperties_c")
        material = fields["f20"]
        require((material["has90"], fields["has88"]) == ((1, 1) if rich else (0, 0)),
                "child visual payload does not match the prospectively chosen appearance profile")
        result = {"packed_colour": fields["f0c"], "default_appearance_flag": fields["f5c"]}
        if rich:
            rv, pbr = material["f90"], fields["f88"]
            result.update({"realview_id": [rv["f00"], rv["f04"]], "resource_locator": rv["f68"],
                           "realview_roughness": rv["f74"], "dspbr_roughness": pbr["f2c"],
                           "dspbr_field_count": len(pbr)})
        else:
            from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import MakeModelVisual
            require(fields == MakeModelVisual().FieldsValue, "part self node does not have its actual constructor appearance")
        roles[role] = result
    require(looks[0] is not looks[1] and looks[1] is not looks[2] and roles["model"] == roles["configuration"],
            "child model/configuration and part self roles are not independently present")
    same_model, model_aliases = compare_typed(looks[0], looks[1])
    holder_delta, holder_aliases = compare_typed(looks[0], looks[2])
    require(not same_model and not model_aliases and not holder_aliases
            and set(holder_delta) == ({
                "moVisualProperties_c/f20/f90/f00", "moVisualProperties_c/f20/f90/f68",
            } if rich else set()),
            "the child model/configuration versus holder appearance changes vary beyond the measured owners")
    return {**info, "part_self_slots": [holder["ref"].IndexValue, base["f58"].IndexValue,
            prop.IndexValue, looks[2].IndexValue, state.IndexValue], "linked_features": keys,
            "appearance_roles": roles, "model_to_holder_typed_delta": holder_delta}


def source_definition(archive):
    raw = archive.require("Contents/Definition")
    source = ReadModelDef(raw, 19000)
    fields = source.GraphValue.DocumentValue.FieldsValue
    manager = fields["f1110"]
    require(WriteModelDef(source.GraphValue).OutputValue == raw
            and fields["has_pwmaterial"] == 1 and manager["list"] == {"n": 0, "items": []},
            "the observed part renderer owner has an unrepresented body")
    try:
        ReadModelDef(raw, 19000, OrdinaryOnly=True)
    except BodyUnsupported as error:
        require(str(error) == RENDERER_REFUSAL, "the native Definition refused at a different source owner")
    else:
        raise ValueError("a source with independent renderer allocation passed ordinary admission")
    return {"exact_replay": True, "strict_guard": RENDERER_REFUSAL,
            "allocator_words": [manager["f08"], manager["f0c"]], "list_count": manager["list"]["n"]}
