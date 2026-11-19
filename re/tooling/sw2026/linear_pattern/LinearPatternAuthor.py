from __future__ import annotations

import math

import Swapp
from AuthorBlindCutSources import BlindCutAuthor
from AuthorCurves import require
from LinearPatternSpecs import expected, rectangle, validate


PLATE_SKETCH, PLATE = "PlateSketch", "PlateBoss"
SEED_SKETCH, SEED, PATTERN = "SeedSketch", "SeedBoss", "LinearPattern"
ROLES = (PLATE_SKETCH, PLATE, SEED_SKETCH, SEED, PATTERN)


class LinearPatternAuthor(BlindCutAuthor):
    def array(self, values, kind):
        return Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | kind, tuple(values))

    def assign(self, obj, name, value, description):
        self.rec.call("set " + name, setattr, obj, name, value, parameters=description)

    def persistent(self, obj, role):
        extension = self.get(self.model, "Extension")
        value = self.get(extension, "GetPersistReference3", obj)
        require(value is not None, f"persistent reference is missing for {role}")
        values = list(value)
        require(0 < len(values) <= 4096 and all(type(item) is int and 0 <= item <= 255 for item in values), f"invalid bounded persistent reference for {role}")
        return {"role": role, "bytes": len(values), "hex": bytes(values).hex()}

    def make_boss(self, case, seed):
        profile = rectangle(case, seed)
        cx, cy = (value / 1000 for value in profile["center_mm"])
        half_width, half_height = profile["width_mm"] / 2000, profile["height_mm"] / 2000
        sketch_name, feature_name = (SEED_SKETCH, SEED) if seed else (PLATE_SKETCH, PLATE)
        self.create_sketch("front", sketch_name, "CreateCornerRectangle", (cx - half_width, cy - half_height, 0.0, cx + half_width, cy + half_height, 0.0), prior_name=PLATE_SKETCH if seed else None)
        depth = case["plate_depth_m"] + (case["seed_extra_depth_m"] if seed else 0.0)
        args = (True, False, False, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        feature = self.get(self.get(self.model, "FeatureManager"), "FeatureExtrusion3", *args)
        require(feature is not None, f"ordinary native boss creation failed: {feature_name}")
        self.set(feature, "Name", feature_name)
        return feature

    def direction_plane(self, case):
        feature = self.get(self.model, "FeatureByName", case["axis_plane"])
        require(feature is not None and self.get(feature, "GetTypeName2") == "RefPlane", "actual named direction plane is missing")
        plane = self.typed(self.get(feature, "GetSpecificFeature2"), "RefPlane")
        return feature, plane

    def build(self, case, session):
        validate(case)
        self.model = self.rec.call("new part", session.new_part)
        self.make_boss(case, False)
        seed = self.make_boss(case, True)
        self.get(self.model, "ClearSelection2", True)
        _, plane = self.direction_plane(case)
        manager = self.get(self.model, "FeatureManager")
        definition = self.typed(self.get(manager, "CreateDefinition", 6), "LinearPatternFeatureData")
        self.assign(definition, "D1Axis", plane, {"actual_principal_plane": case["axis_plane"], "binding": "IRefPlane from this document"})
        self.assign(definition, "PatternFeatureArray", self.array((seed,), Swapp.pythoncom.VT_DISPATCH), {"actual_seed_feature": SEED, "array_element_type": "VT_DISPATCH"})
        self.set(definition, "BodyPattern", False)
        self.set(definition, "GeometryPattern", False)
        self.set(definition, "VarySketch", False)
        self.set(definition, "InstancesToVary", False)
        self.set(definition, "D1EndCondition", 0)
        self.set(definition, "D1Spacing", case["spacing_m"])
        self.set(definition, "D1TotalInstances", case["instances"])
        self.set(definition, "D1ReverseDirection", case["reverse"])
        optional = {"direction2_specified": bool(self.get(definition, "IsDirection2Specified")), "direction2_axis_is_null": self.get(definition, "D2Axis") is None, "skipped_items": list(self.get(definition, "SkippedItemArray") or ())}
        self.rec.data["fresh_definition_optional_state"] = optional
        self.rec.flush()
        require(not optional["direction2_specified"] and optional["direction2_axis_is_null"] and not optional["skipped_items"], "fresh ordinary definition has a specified second direction or skipped instances")
        feature = self.get(manager, "CreateFeature", definition)
        require(feature is not None, "ordinary native part-feature linear pattern creation returned null")
        self.set(feature, "Name", PATTERN)
        self.get(self.model, "ClearSelection2", True)

    def transform_point(self, coordinates, transform):
        utility = self.get(self.app, "GetMathUtility")
        point = self.get(utility, "CreatePoint", self.array(coordinates, Swapp.pythoncom.VT_R8))
        return [float(value) for value in self.get(self.get(point, "MultiplyTransform", transform), "ArrayData")]

    def transform_vector(self, coordinates, transform):
        utility = self.get(self.app, "GetMathUtility")
        vector = self.get(utility, "CreateVector", self.array(coordinates, Swapp.pythoncom.VT_R8))
        return [float(value) for value in self.get(self.get(vector, "MultiplyTransform", transform), "ArrayData")]

    def direction(self, case, sketch, plane):
        plane_transform = self.get(plane, "Transform")
        model_to_sketch = self.get(sketch, "ModelToSketchTransform")
        normal_world = self.transform_vector([0.0, 0.0, 1.0], plane_transform)
        normal_sketch = self.transform_vector(normal_world, model_to_sketch)
        length = math.sqrt(sum(value * value for value in normal_sketch))
        require(math.isfinite(length) and length > 0, "principal direction transform has no finite normal")
        normal_sketch = [value / length for value in normal_sketch]
        axis = case["direction_component"]
        require(abs(abs(normal_sketch[axis]) - 1.0) < 1e-10 and all(abs(normal_sketch[index]) < 1e-10 for index in range(3) if index != axis), "actual principal plane normal is outside the authored local direction")
        direction = [value * (-1 if case["reverse"] else 1) for value in normal_sketch]
        return direction, {
            "reference_plane_transform": list(self.get(plane_transform, "ArrayData")),
            "reference_plane_normal_model": normal_world, "reference_plane_normal_sketch": normal_sketch,
            "reverse": case["reverse"], "signed_direction_sketch": direction,
            "semantic_check": "independent analytical centre of mass must agree; no observed centroid selects the direction sign",
        }

    def observe_dimensions(self, feature, spacing, instances):
        rows, objects = [], {}
        display = self.get(feature, "GetFirstDisplayDimension")
        while display is not None:
            require(len(rows) < 32, "pattern display-dimension traversal exceeded its bound")
            dimension = self.typed(self.get(display, "GetDimension2", 0), "Dimension")
            name = str(self.get(dimension, "FullName"))
            require(name not in objects and name.split("@")[1:2] == [PATTERN], "pattern dimension identity or feature owner is ambiguous")
            row = {"full_name": name, "value": float(self.get(dimension, "SystemValue")), "read_only": bool(self.get(dimension, "ReadOnly")), "driven_state": int(self.get(dimension, "DrivenState")), "display_reference": self.persistent(display, "pattern display dimension")}
            rows.append(row)
            objects[name] = dimension
            display = self.get(feature, "GetNextDisplayDimension", display)
        bindings = {}
        for role, target in (("spacing", spacing), ("instances", instances)):
            matches = [row for row in rows if math.isclose(row["value"], target, rel_tol=2e-7, abs_tol=1e-12)]
            require(len(matches) == 1, f"one actual {role} dimension is required; unused direction dimensions must not collide")
            row = matches[0]
            require(not row["read_only"] and row["driven_state"] == 2, f"actual {role} dimension is not driving and editable")
            bindings[role] = row["full_name"]
        return {"all": rows, "bindings": bindings}, objects

    def inspect_pattern(self, case, spacing, instances):
        feature = self.get(self.model, "FeatureByName", PATTERN)
        require(feature is not None, "named linear-pattern feature is missing")
        definition = self.typed(self.get(feature, "GetDefinition"), "LinearPatternFeatureData")
        accessed = bool(self.get(definition, "AccessSelections", self.model, Swapp.nothing()))
        require(accessed, "linear-pattern definition selection access failed")
        try:
            axis = self.get(definition, "D1Axis")
            require(axis is not None, "actual direction-one reference is missing")
            axis = self.typed(axis, "RefPlane")
            plane_feature, plane = self.direction_plane(case)
            axis_reference = self.persistent(axis, "definition direction-one plane")
            plane_reference = self.persistent(plane, "authored direction-one plane")
            require(axis_reference["hex"] == plane_reference["hex"], "pattern resolved another actual direction plane")
            values = {key: self.get(definition, key) for key in ("D1Spacing", "D1TotalInstances", "D1ReverseDirection", "D1EndCondition", "D2Spacing", "D2TotalInstances", "BodyPattern", "GeometryPattern", "VarySketch", "InstancesToVary", "FeatureScope", "AutoSelect")}
            self.rec.close_number("actual D1 spacing", values["D1Spacing"], spacing)
            require(type(values["D1TotalInstances"]) is int and values["D1TotalInstances"] == instances and bool(values["D1ReverseDirection"]) == case["reverse"] and values["D1EndCondition"] == 0, "native pattern changed the authored direction-one inputs")
            require(not any(bool(values[key]) for key in ("BodyPattern", "GeometryPattern", "VarySketch", "InstancesToVary")), "pattern left the ordinary feature-copy scope")
            direction2 = self.get(definition, "D2Axis")
            require(direction2 is None and not self.get(definition, "IsDirection2Specified"), "unexpected second pattern direction")
            skipped = list(self.get(definition, "SkippedItemArray") or ())
            require(not skipped and int(self.get(definition, "GetSkippedItemCount")) == 0, "ordinary source acquired skipped instances")
            seeds = list(self.get(definition, "PatternFeatureArray") or ())
            require(len(seeds) == int(self.get(definition, "GetPatternFeatureCount")) == 1, "ordinary pattern must retain one seed feature")
            seed_name = str(self.get(seeds[0], "Name"))
            expected_seed = self.get(self.model, "FeatureByName", SEED)
            seed_reference = self.persistent(seeds[0], "definition seed feature")
            require(seed_name == SEED and seed_reference["hex"] == self.persistent(expected_seed, "authored seed feature")["hex"], "pattern seed is not the authored boss feature")
            scope_bodies = list(self.get(definition, "FeatureScopeBodies") or ())
            result = {"type": str(self.get(feature, "GetTypeName2")), "legacy_type": str(self.get(feature, "GetTypeName")), "values": values, "axis_type": int(self.get(definition, "GetD1AxisType")), "axis_reference": axis_reference, "plane_reference": plane_reference, "plane_feature_reference": self.persistent(plane_feature, "direction plane feature"), "pattern_reference": self.persistent(feature, "linear pattern feature"), "seeds": [{"name": seed_name, "reference": seed_reference}], "skipped_items": skipped, "feature_scope_body_count": len(scope_bodies), "selection_access": True}
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        result["dimensions"], _ = self.observe_dimensions(feature, spacing, instances)
        result["parents"] = [str(self.get(parent, "Name")) for parent in self.get(feature, "GetParents") or ()]
        require(SEED in result["parents"], "pattern dependency tree lost its actual seed feature")
        return result

    def extreme_bounds(self):
        bodies = list(self.get(self.model, "GetBodies2", 0, False) or ())
        require(len(bodies) == 1, "exact extrema require one actual solid body")
        result = [0.0] * 6
        observations = []
        for axis in range(3):
            for sign in (-1, 1):
                direction = [0.0] * 3
                direction[axis] = sign
                coordinates = [Swapp.VARIANT(Swapp.pythoncom.VT_BYREF | Swapp.pythoncom.VT_R8, 0.0) for _ in range(3)]
                success = self.get(bodies[0], "GetExtremePoint", *direction, *coordinates)
                require(bool(success), "actual body failed exact extreme-point query")
                point = [float(value.value) for value in coordinates]
                require(all(math.isfinite(value) for value in point), "nonfinite body extreme point")
                result[axis + (3 if sign > 0 else 0)] = point[axis]
                observations.append({"direction": direction, "point": point})
        vertices = list(self.get(bodies[0], "GetVertices") or ())
        require(0 < len(vertices) <= 4096, "solid vertex inventory is absent or exceeds its bound")
        points = [[float(value) for value in self.get(vertex, "GetPoint")] for vertex in vertices]
        require(all(len(point) == 3 and all(math.isfinite(value) for value in point) for point in points), "invalid solid vertex coordinates")
        return {"minmax": result, "exact_extreme_points": observations, "approximate_body_box": list(self.get(bodies[0], "GetBodyBox")), "faces": len(list(self.get(bodies[0], "GetFaces") or ())), "vertices": points}

    def snapshot(self, case, label, spacing, instances):
        require(self.get(self.model, "ForceRebuild3", False), "ordinary pattern rebuild failed")
        require(int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0, "document has rebuild errors or warnings")
        tree = self.feature_tree(required_names=ROLES)
        active_names = [row["name"] for row in tree if not row["suppressed"]]
        require(active_names.index(PLATE) < active_names.index(SEED) < active_names.index(PATTERN), "authored solid feature order changed")
        plate, inverse = self.inspect_profile(PLATE_SKETCH, rectangle(case, False))
        seed, _ = self.inspect_profile(SEED_SKETCH, rectangle(case, True))
        for index, pair in enumerate(zip(plate["model_to_sketch"], seed["model_to_sketch"], strict=True)):
            self.rec.close_number(f"shared front frame element {index}", *pair)
        plate_feature = self.get(self.model, "FeatureByName", PLATE_SKETCH)
        plate_sketch = self.get(plate_feature, "GetSpecificFeature2")
        _, plane = self.direction_plane(case)
        direction, direction_record = self.direction(case, plate_sketch, plane)
        analytical = expected(case, spacing, instances, direction)
        mass = self.rec.call("mass properties", Swapp.mass, self.model)
        require(self.rec.call("solid body count", Swapp.bodies, self.model) == 1 and mass is not None and "error" not in mass, "pattern lacks one measurable solid body")
        self.rec.close_number(label + " volume", mass["volume"], analytical["volume"], absolute=1e-22)
        self.rec.close_number(label + " area", mass["area"], analytical["area"], absolute=1e-18)
        target_com = self.transform_point(analytical["com_sketch"], inverse)
        for axis, pair in enumerate(zip(mass["com"], target_com, strict=True)):
            self.rec.close_number(f"{label} centre of mass {axis}", *pair, absolute=1e-10)
        corners = [self.transform_point(point, inverse) for point in analytical["corners_sketch"]]
        target_box = [min(point[axis] for point in corners) for axis in range(3)] + [max(point[axis] for point in corners) for axis in range(3)]
        bounds = self.extreme_bounds()
        for axis, pair in enumerate(zip(bounds["minmax"], target_box, strict=True)):
            self.rec.close_number(f"{label} exact body bound {axis}", *pair, absolute=1e-9)
        unmatched = list(bounds["vertices"])
        require(len(unmatched) == len(corners), "native solid vertex count differs from the independent plate-plus-boss topology")
        for index, point in enumerate(corners):
            matches = [other for other in unmatched if all(abs(a - b) <= 1e-9 for a, b in zip(point, other, strict=True))]
            require(len(matches) == 1, f"one actual vertex is required for analytical corner {index}")
            unmatched.remove(matches[0])
        require(not unmatched, "solid has unaccounted occurrence-placement vertices")
        snapshot = {"tree": tree, "plate_profile": plate, "seed_profile": seed, "plate_boss": self.inspect_feature(PLATE, PLATE_SKETCH, case["plate_depth_m"] * 1000, True), "seed_boss": self.inspect_feature(SEED, SEED_SKETCH, (case["plate_depth_m"] + case["seed_extra_depth_m"]) * 1000, True), "pattern": self.inspect_pattern(case, spacing, instances), "direction": direction_record, "bodies": 1, "mass": mass, "bounds": bounds, "expected": {**analytical, "com_model": target_com, "bbox_model": target_box}}
        self.rec.data[label] = snapshot
        self.rec.flush()
        return snapshot

    def edit(self, case, role):
        feature = self.get(self.model, "FeatureByName", PATTERN)
        observed, objects = self.observe_dimensions(feature, case["spacing_m"], case["instances"])
        name = observed["bindings"][role]
        dimension = objects[name]
        target = case["edit_spacing_m"] if role == "spacing" else case["edit_instances"]
        status = int(self.get(dimension, "SetSystemValue3", target, 1, Swapp.nothing()))
        require(status == 0, f"actual {role} driving-dimension setter failed: {status}")
        self.rec.close_number("edited actual " + role + " dimension", self.get(dimension, "SystemValue"), target)
        self.rec.data["edit"] = {"role": role, "actual_dimension_full_name": name, "new_value": target, "setter_status": status, "pristine_branch": True}
        self.rec.flush()
