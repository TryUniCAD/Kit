from collections.abc import Mapping

from Core import Obj
from SdkPlanarFaults import RejectedInput, apply_fault, state_snapshot
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeMateMut import MakeMateMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateChild import MateChild
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import MateContext
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateSelection import MateSelection
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import PlanarMateIn
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


def compatible(value, memo):
    if isinstance(value, Obj):
        return value
    if isinstance(value, ArchiveNode):
        if id(value) not in memo:
            node = Obj(value.ClassValue.NameValue, schema=value.ClassValue.SchemaValue)
            memo[id(value)] = node
            node.f.update({name: compatible(item, memo) for name, item in value.FieldsValue.items()})
        return memo[id(value)]
    if isinstance(value, Mapping):
        return {name: compatible(item, memo) for name, item in value.items()}
    if isinstance(value, tuple):
        return tuple(compatible(item, memo) for item in value)
    if isinstance(value, list):
        return [compatible(item, memo) for item in value]
    return value


class PlanarBridge:
    def __init__(self, document_module, fault=None):
        self.module = document_module
        self.original_factory = document_module.aligned_planar_mate
        self.original_resolved = document_module.store_resolved_state
        self.original_mates = document_module.store_assembly_mates
        self.result = None
        self.resolved_doc = None
        self.report = None
        self.fault = fault
        self.rejection = None

    def install(self):
        self.module.aligned_planar_mate = self.make_mate
        self.module.store_resolved_state = self.store_resolved
        self.module.store_assembly_mates = self.store_mates

    def restore(self):
        self.module.aligned_planar_mate = self.original_factory
        self.module.store_resolved_state = self.original_resolved
        self.module.store_assembly_mates = self.original_mates

    def make_mate(self, *, assembly, group, occurrences, child, model_header, configuration, allocator, target, request, created_at, dimension_presentation=None):
        child_value = MateChild(child.model, child.model_header, child.configuration, tuple(child.features))
        by_name = {node["f18"]["f08"]: node for node in child.features if node.cls == "moRefPlane_c" and isinstance(node.get("f6f8"), Obj) and node["f6f8"].cls == "moDefaultRefPlnData_c"}
        selections = tuple(MateSelection(occurrences[row["occurrence"]], child_value, by_name[row["datum"]]) for row in request["endpoints"])
        ids = PersistentIds(NextValue=allocator.next_id, Reserved=tuple(sorted(allocator._reserved)))
        context = MateContext(assembly, group, model_header, configuration, FeatureTarget(target["date_code"], target["parasolid_version"]), ids)
        inputs = PlanarMateIn(request["kind"], request["name"], selections, occurrences[request["fixed_occurrence"]], created_at)
        context, inputs = apply_fault(self.fault, context, inputs)
        before = state_snapshot(context, inputs)
        try:
            node = MakeMateMut(context, inputs)
        except (ValueError, TypeError) as error:
            if self.fault is None:
                raise
            after = state_snapshot(context, inputs)
            if after != before:
                raise ValueError("rejected SDK mate input changed persistent parent state") from error
            self.rejection = {"fault": self.fault, "error_type": type(error).__name__, "error": str(error), "parent_state_unchanged": True, "before": before, "after": after}
            raise RejectedInput(str(error)) from error
        if self.fault is not None:
            raise ValueError("SDK mate construction admitted its declared malformed input")
        result = compatible(node, {})
        expected_id = result["f08"]
        result["f08"] = -1
        if allocator.allocate(result) != expected_id or allocator.next_id != ids.NextValue:
            raise ValueError("shared persistent allocator differs from the unchanged composer")
        wrappers = [row["o"] for row in node.FieldsValue["f410"]]
        planes = [row["o"] for row in node.FieldsValue["f3c8"]]
        if any(wrapper.FieldsValue["f10"] is wrapper.FieldsValue["f18"] for wrapper in wrappers):
            raise ValueError("resolved wrapper caches share mutable transform storage")
        for wrapper, selection in zip(wrappers, selections, strict=True):
            if wrapper.FieldsValue["f10"] is selection.OccurrenceValue.FieldsValue["f360"]:
                raise ValueError("resolved wrapper aliases its occurrence transform storage")
            if wrapper.FieldsValue["f10"].get("has_matrix") and (wrapper.FieldsValue["f10"]["f08"] is wrapper.FieldsValue["f18"]["f08"] or wrapper.FieldsValue["f10"]["f08"] is selection.OccurrenceValue.FieldsValue["f360"]["f08"]):
                raise ValueError("resolved wrapper matrix storage is shared")
        self.result = node
        components = [value.FieldsValue["f58"].FieldsValue["f58"] for value in planes]
        if components[0] is components[1] or any(value is assembly["f990"] or value.FieldsValue["owner"] is not assembly for value in components):
            raise ValueError("detached plane references lost exclusive owned components")
        self.report = {"native_class": node.ClassValue.NameValue, "persistent_id": expected_id, "next_persistent_id": ids.NextValue, "next_wrapper_id": assembly["fd48"], "ordered_occurrence_ids": [value.OccurrenceValue["f08"] for value in selections], "ordered_datum_ids": [value.DatumValue["f08"] for value in selections], "independent_transform_caches": True, "distinct_resolved_wrappers": wrappers[0] is not wrappers[1], "distinct_detached_wrappers": planes[0] is not planes[1], "exclusive_detached_components": True, "unregistered_detached_planes": [value.FieldsValue["f58"].FieldsValue["ff8"].FieldsValue["f08"] for value in planes], "parent_owner_identity": all(value.FieldsValue["f58"].FieldsValue["f58"].FieldsValue["owner"] is assembly for value in wrappers), "actual_occurrence_backlinks": all(wrapper.FieldsValue["f58"].FieldsValue["f58"].FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"] is selected.OccurrenceValue["f4f8"] for wrapper, selected in zip(wrappers, selections, strict=True)), "fixed_flags": [value["f408"] for value in occurrences]}
        return result

    def store_resolved(self, doc, registry, version, *, seed):
        self.resolved_doc = doc
        return self.original_resolved(doc, registry, version, seed=seed)

    def store_mates(self, *, registry, resolved_map, mate_group, mates):
        if self.result is None or self.resolved_doc is None:
            raise ValueError("SDK mate stream requires its actual constructed graph and resolved context")
        doc = self.resolved_doc
        graph = ResolvedGraph(tuple(doc.roots), None, resolved_map.state, doc.head["base"], 19000, dict(doc.head["context"]), {})
        payload, result = WriteMatesMut((self.result,), graph)
        self.report["sdk_mates_write"] = dict(result.ReportValue)
        self.report["map_base"] = result.MapBase
        self.report["map_terminal"] = result.MapValue.CounterValue
        self.report["mate_stream_bytes"] = len(payload)
        return payload
