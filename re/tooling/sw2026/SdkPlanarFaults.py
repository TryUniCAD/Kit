from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


class RejectedInput(ValueError):
    pass


FAULT_NAMES = (
    "foreign_occurrence", "wrong_external_backlink", "wrong_child_configuration",
    "stale_child_update", "wrong_datum_owner", "unregistered_datum", "bad_datum_bounds",
    "scaled_placement", "reflected_placement", "repeated_selection", "foreign_fixed_input",
    "wrong_allocator_boundary", "wrapper_counter_exhausted", "unsupported_kind",
    "invalid_mate_name", "invalid_creation_epoch", "unsupported_parent_schema",
    "unsupported_child_schema", "unsupported_datum_version",
    "overflowing_inverse_frame",
)


def state_snapshot(context, inputs):
    parent = context.AssemblyValue
    occurrences = [row["o"] for row in parent["f68"]["list"]["items"]]
    return {
        "allocator_next": context.Allocator.NextValue,
        "allocations": len(context.Allocator.Allocations),
        "wrapper_counter": parent["fd48"],
        "fixed_flags": [value["f408"] for value in occurrences],
        "header_next": context.HeaderValue["f08"],
        "selected_ids": [value.OccurrenceValue.FieldsValue["f08"] for value in inputs.Selections],
    }


def apply_fault(name, context, inputs):
    if name is None:
        return context, inputs
    if name not in FAULT_NAMES:
        raise ValueError("unknown SDK construction fault")
    first, second = inputs.Selections
    occurrence = first.OccurrenceValue
    datum = first.DatumValue
    if name == "foreign_occurrence":
        foreign = ArchiveNode(occurrence.ClassValue, dict(occurrence.FieldsValue))
        inputs = replace(inputs, Selections=(replace(first, OccurrenceValue=foreign), second))
    elif name == "wrong_external_backlink":
        occurrence["f4f8"]["f50"] = second.OccurrenceValue
    elif name == "wrong_child_configuration":
        occurrence["f3c0"]["f10"] += 1
    elif name == "stale_child_update":
        occurrence["f3e0"] ^= 1
    elif name == "wrong_datum_owner":
        datum["owner"] = context.AssemblyValue
    elif name == "unregistered_datum":
        datum["f08"] = -1
    elif name == "bad_datum_bounds":
        datum["f6f8"]["b0"] = float("nan")
    elif name == "scaled_placement":
        occurrence["f360"]["f70"] = 2.0
    elif name == "reflected_placement":
        occurrence["f360"].update(has_matrix=1, f08={f"m{i}": float(i in (0, 4, 8)) * (-1 if i == 0 else 1) for i in range(9)})
    elif name == "repeated_selection":
        inputs = replace(inputs, Selections=(first, first))
    elif name == "foreign_fixed_input":
        inputs = replace(inputs, FixedValue=ArchiveNode(occurrence.ClassValue, dict(occurrence.FieldsValue)))
    elif name == "wrong_allocator_boundary":
        context = replace(context, Allocator=PersistentIds(context.Allocator.NextValue + 1))
    elif name == "wrapper_counter_exhausted":
        context.AssemblyValue["fd48"] = 0x7FFFFFFE
    elif name == "unsupported_kind":
        inputs = replace(inputs, KindValue="distance")
    elif name == "invalid_mate_name":
        inputs = replace(inputs, NameValue="invalid\x00name")
    elif name == "invalid_creation_epoch":
        inputs = replace(inputs, CreatedValue=-1)
    elif name == "unsupported_parent_schema":
        context.AssemblyValue.ClassValue = RuntimeClass("moAssembly_c", 2)
    elif name == "unsupported_child_schema":
        datum.ClassValue = RuntimeClass("moRefPlane_c", 2)
    elif name == "unsupported_datum_version":
        datum["f2b0"] = 18000
    elif name == "overflowing_inverse_frame":
        occurrence["f360"].update(f58=1.6e308, f60=1.6e308, f68=0.0)
    return context, inputs
