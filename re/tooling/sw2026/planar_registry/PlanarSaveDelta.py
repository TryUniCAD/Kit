from collections import Counter

from PlanarRegistryBuild import require
from PlanarRendererInput import differences, material_id, observe_looks
from PlanarVisualOwners import node, parent_store, read_parent_store
from para.concentric.AuditConcentricDisplayState import compare_typed, model_inputs
from para.concentric.MakeVisualStateStore import STREAM
from para.concentric.ProveVisualStateStore import replay
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


PARENT_REFUSAL = "compound occurrence loses its live identity, order word, pooled file or visibility"
LIVE_ID = "f20.f90.f00"


def refuse_constructor_order(saved, registry):
    try:
        parent_store(saved, registry)
    except ValueError as error:
        require(str(error) == PARENT_REFUSAL, "original constructor observer has a different refusal")
        return str(error)
    raise ValueError("original constructor observer accepted a native-saved context")


def save_order(context, occurrence):
    return context["f30"] == 101 and occurrence["f3f0"] == 102


def parent_delta(frozen, saved, registry, count):
    prior = parent_store(frozen, registry)
    original_refusal = refuse_constructor_order(saved, registry)
    actual = read_parent_store(saved, registry, save_order)
    prior_rows, actual_rows = (row["occurrence_rows_in_wire_order"] for row in (prior, actual))
    require(len(prior_rows) == len(actual_rows) == count and count in (2, 3), "unexpected disclosed occurrence count")
    require(all(before[:2] == after[:2] and before[3] == after[3] and (before[2], after[2]) == (203, 101)
                for before, after in zip(prior_rows, actual_rows, strict=True)), "saved compound owners moved")
    stable = set(prior) - {"occurrence_rows_in_wire_order", "sha256"}
    require(all(prior[key] == actual[key] for key in stable), "saved visual parent differs outside its measured owners")
    old_live, new_live = (model_inputs(archive)[0] for archive in (frozen, saved))
    require(tuple(old_live) == tuple(new_live) and all(old_live[key].FieldsValue["f3f0"]
            == new_live[key].FieldsValue["f3f0"] == 102 for key in old_live), "actual live reference stamps differ")
    prior_graph, saved_graph = (replay(archive, registry)[0] for archive in (frozen, saved))
    original_root, saved_root = (doc.head["root"] for doc in (prior_graph, saved_graph))
    delta, aliases = compare_typed(original_root, saved_root)
    reverse, reverse_aliases = compare_typed(saved_root, original_root)
    expected = {}
    for index in range(count):
        prefix = f"visStateKeyData_c/comps/{index}/comp/moContextChainComponent_c/"
        expected[prefix + "f30"] = [203, 101]
        expected[prefix + "f40/moExtObject_c/f58"] = [0, 8]
    require(delta == expected and not aliases and not reverse_aliases
            and reverse == {key: list(reversed(value)) for key, value in expected.items()},
            "native save varied the parent visual graph or aliases beyond the measured context fields")
    raw_before, raw_after = (archive.require(STREAM) for archive in (frozen, saved))
    changed_bytes = [(index, left, right) for index, (left, right) in enumerate(zip(raw_before, raw_after, strict=True))
                     if left != right]
    require(Counter((left, right) for _, left, right in changed_bytes) == Counter({(203, 101): count, (0, 8): count}),
            "native save byte changes do not match the typed context pair")
    return {**actual, "frozen_visual_sha256": prior["sha256"], "original_observer_refusal": original_refusal,
            "live_occurrence_order_word": 102, "typed_context_deltas": delta,
            "byte_deltas": changed_bytes, "aliases_preserved_in_both_directions": True}


def child_delta(frozen, saved, registry):
    source, initial_manager, first = observe_looks(frozen, registry, generated=True)
    actual, saved_manager, last = observe_looks(saved, registry)
    typed = {name: list(differences(a, b)) for name, a, b in zip(("model", "configuration", "holder"), source, actual, strict=True)}
    require(typed == {"model": [LIVE_ID], "configuration": [LIVE_ID], "holder": []},
            "saved rendering payload differs outside the two live ID fields")
    before, after = (list(map(material_id, values)) for values in (source, actual))
    initial = initial_manager.AppearanceValue.NextAppearanceId
    following = saved_manager.AppearanceValue.NextAppearanceId
    require(before[0] == before[1] == before[2] + 1 and initial == before[0] + 1
            and after[0] == after[1] == before[0] + 3 and after[2] == before[2] and following == after[0] + 1
            and following == initial + 3 and initial_manager.BomOnWire is saved_manager.BomOnWire is True,
            "saved detached holder live IDs or Definition cursor differ from the disclosed transition")
    require(first["sha256"] == last["sha256"] and first["terminal_map"] == last["terminal_map"]
            and frozen.require(STREAM) == saved.require(STREAM) and first["physical_density_parameter"] is None
            and last["physical_density_parameter"] == [1000.0, 0]
            and first["active_configuration_density"] == last["active_configuration_density"] == -1.0,
            "saved child VisualStates or independent density owner differs")
    link = ReadNativeLink(saved, 0)
    material = link.ConfigValue.RootValue.FieldsValue["f1420"]
    density = node(material, "moMaterial_c")["f08"]
    density_owners = [[value.ClassValue.NameValue, value.IndexValue, value.StartOffset, value.EndOffset]
                      for value in (material, density)]
    require(density_owners == [["moMaterial_c", 51, 2868, 2945], ["moDensityParameter_c", 53, 2886, 2945]],
            "saved child density owners moved in Config-0")
    return {"physical_density_parameter": [None, last["physical_density_parameter"]], "configuration_density": -1.0,
            "config_0_density_owners": density_owners,
            "child_visualstates_sha256": last["sha256"], "child_visualstates_unchanged": True,
            "renderer_field_deltas": typed, "id_roles": ["model", "configuration", "holder"],
            "frozen_ids": before, "saved_ids": after, "definition_cursor": [initial, following],
            "original_allocator_retention_passed": False}
