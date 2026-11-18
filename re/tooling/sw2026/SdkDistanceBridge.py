from dataclasses import replace

import SdkPlanarBridge
from SdkPlanarBridge import PlanarBridge
from SdkPlanarFaults import apply_fault
from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import DistanceInput
from convert.adapters.solidworks.Archive.Construction.PlanarDistance.MakeDistMateMut import MakeDistMateMut


EXTRA_FAULTS = (
    "zero_length", "negative_length", "short_length", "nonfinite_length", "boolean_length",
    "invalid_design_intent", "invalid_leader", "nonpositive_separation", "opposite_normals",
    "unsupported_tolerance", "centered_text", "insufficient_id_room",
)


class DistanceIds:
    def __init__(self, original):
        self.original = original
        self._reserved = original._reserved

    @property
    def next_id(self):
        return self.original.next_id

    def allocate(self, node):
        if node.cls != "moMateDistanceDim_c":
            raise ValueError("distance bridge requires its real distance mate")
        dimension = node["f4b8"]["f850"][0]["o"]["ff0"]
        dimension_id = dimension["f50"]
        dimension["f50"] = -1
        if self.original.allocate(dimension, field="f50") != dimension_id:
            raise ValueError("SDK distance consumed a different dimension identity")
        return self.original.allocate(node)


class DistanceBridge(PlanarBridge):
    def make_mate(self, **values):
        self.authored_distance = values["request"]["distance_m"]
        self.presentation = dict(values["dimension_presentation"])
        factory, fault = SdkPlanarBridge.MakeMateMut, SdkPlanarBridge.apply_fault
        SdkPlanarBridge.MakeMateMut = self.construct_distance
        SdkPlanarBridge.apply_fault = self.apply_distance_fault
        try:
            result = super().make_mate(**{**values, "allocator": DistanceIds(values["allocator"])})
        finally:
            SdkPlanarBridge.MakeMateMut, SdkPlanarBridge.apply_fault = factory, fault
        display = self.result.FieldsValue["f4b8"]
        handle = display.FieldsValue["f850"][0]["o"]
        dimension = handle.FieldsValue["ff0"]
        parameter = dimension.FieldsValue["f28"]
        if any(value.FieldsValue["owner"] is not self.result for value in (display, handle, dimension, parameter)):
            raise ValueError("SDK driving distance lost actual feature owners")
        if parameter.FieldsValue["f08"] != -1 or dimension.FieldsValue["refcount"] != len(dimension.FieldsValue["retaining_handles"]):
            raise ValueError("SDK driving parameter consumed an id or lost its retaining handle")
        if dimension.FieldsValue["f50"] >= self.result.FieldsValue["f08"]:
            raise ValueError("SDK driving dimension must allocate before its mate")
        self.report["driving_distance"] = {
            "dimension_id": dimension.FieldsValue["f50"], "mate_id": self.result.FieldsValue["f08"],
            "parameter_id": parameter.FieldsValue["f08"], "parameter_name": parameter.FieldsValue["f18"].FieldsValue["f08"],
            "value_metres": parameter.FieldsValue["f58"], "actual_feature_owners": True,
            "actual_local_dimension": handle.FieldsValue["fe8"] is None and handle.FieldsValue["f100"] is None,
            "actual_retaining_handle": dimension.FieldsValue["retaining_handles"][0] is handle,
            "retaining_handle_count": dimension.FieldsValue["refcount"], "text_kind": display.FieldsValue["f6a0"]["f10"],
            "selected_leader": display.FieldsValue["ff80"], "design_intent": bool(display.FieldsValue["fb60"] & 0x100),
            "constructor_value_cache": display.FieldsValue["fad0"],
        }
        return result

    def construct_distance(self, context, inputs):
        value = self.authored_distance
        design_intent = self.presentation["design_intent"]
        leader = self.presentation["selected_leader"]
        if self.fault == "zero_length":
            value = 0.0
        elif self.fault == "negative_length":
            value = -0.01
        elif self.fault == "short_length":
            value = 1e-15
        elif self.fault == "nonfinite_length":
            value = float("inf")
        elif self.fault == "boolean_length":
            value = True
        elif self.fault == "invalid_design_intent":
            design_intent = 1
        elif self.fault == "invalid_leader":
            leader = 1 << 31
        return MakeDistMateMut(context, inputs, DistanceInput(value, design_intent, leader))

    def apply_distance_fault(self, name, context, inputs):
        if name == "unsupported_kind":
            return context, replace(inputs, KindValue="parallel")
        if name not in EXTRA_FAULTS:
            return apply_fault(name, context, inputs)
        if name == "nonpositive_separation":
            first, second = inputs.Selections
            second.OccurrenceValue["f360"] = dict(first.OccurrenceValue["f360"])
        elif name == "opposite_normals":
            second = inputs.Selections[1].OccurrenceValue
            second["f360"].update(has_matrix=1, f08={f"m{i}": float(i in (0, 4, 8)) * (-1 if i in (0, 4) else 1) for i in range(9)})
        elif name in ("unsupported_tolerance", "centered_text"):
            details = context.AssemblyValue["fae0"]["f13b0"]
            if name == "unsupported_tolerance":
                details["fe0"]["f44"] = 1
            else:
                details["fd8"] |= 2
        elif name == "insufficient_id_room":
            context.HeaderValue["f08"] = 0x7FFFFFFE
            context.Allocator.CounterValue = 0x7FFFFFFE
        return context, inputs
