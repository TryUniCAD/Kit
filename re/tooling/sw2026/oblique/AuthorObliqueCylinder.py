from math import sqrt

from AuthorCurves import CurveAuthor, require
from AuthorAssemblySources import feature_tree
from ObliqueCylinderPlan import (
    EDITS,
    NAMES,
    PRINCIPALS,
    angle_arguments,
    boss_arguments,
    prediction,
)
from ReferencePlaneDimensions import circle_geometry
from ObliqueCylinderInvoke import invoke


class ObliqueAuthor(CurveAuthor):
    def __init__(self, application, recorder, modules, api, predictions):
        super().__init__(application, recorder, modules)
        self.api = api
        self.predictions = predictions

    def declared_interface(self, value, name):
        require(value is not None, "null native interface " + name)
        iid = self.sw.pythoncom.MakeIID(self.api["interfaces"][name]["guid"])
        proxy = self.rec.call(
            "query declared " + name,
            value._oleobj_.QueryInterface,
            iid,
            self.sw.pythoncom.IID_IDispatch,
            parameters={"interface": name, "iid": str(iid)},
        )
        return self.sw.wc.Dispatch(proxy)

    def feature(self, name):
        part = self.declared_interface(self.model, "IPartDoc")
        value = self.get(part, "FeatureByName", name)
        require(
            value is not None and str(self.get(value, "Name")) == name,
            "missing actual feature owner " + name,
        )
        return value

    def top_features(self):
        result = []
        value = self.get(self.model, "FirstFeature")
        while value is not None:
            require(
                len(result) < 256,
                "oblique feature traversal exceeded its bounded profile",
            )
            result.append(
                (
                    value,
                    str(self.get(value, "Name")),
                    str(self.get(value, "GetTypeName2")),
                )
            )
            value = self.get(value, "GetNextFeature")
        return result

    def parents(self, value):
        return [
            {
                "name": str(self.get(item, "Name")),
                "type": str(self.get(item, "GetTypeName2")),
            }
            for item in self.get(value, "GetParents") or ()
        ]

    def select(self, entries):
        self.get(self.model, "ClearSelection2", True)
        manager = self.get(self.model, "SelectionManager")
        observations = []
        for ordinal, (name, mark) in enumerate(entries):
            actual = self.feature(name)
            require(
                bool(self.get(actual, "Select2", bool(ordinal), mark)),
                "actual feature selection failed: " + name,
            )
            selected = self.get(manager, "GetSelectedObject6", ordinal + 1, -1)
            require(selected is not None, "native selection lost its actual object")
            actual_mark = int(self.get(manager, "GetSelectedObjectMark", ordinal + 1))
            require(actual_mark == mark, "native selection mark differs")
            observations.append(
                {
                    "expected_feature": name,
                    "mark": actual_mark,
                    "native_selected_type": int(
                        self.get(manager, "GetSelectedObjectType3", ordinal + 1, -1)
                    ),
                }
            )
        require(
            int(self.get(manager, "GetSelectedObjectCount2", -1)) == len(entries),
            "unexpected selected native objects",
        )
        self.rec.data.setdefault("selection_sets", []).append(observations)
        self.rec.flush()

    def create_axis(self, name, parents):
        before = {name for _, name, kind in self.top_features() if kind == "RefAxis"}
        self.select([(parent, 0) for parent in parents])
        require(
            bool(self.get(self.model, "InsertAxis2", True)),
            "two-plane reference axis creation failed",
        )
        new = [
            value
            for value, name, kind in self.top_features()
            if kind == "RefAxis" and name not in before
        ]
        require(
            len(new) == 1, "two-plane axis did not publish exactly one actual feature"
        )
        self.set(new[0], "Name", name)
        actual_parents = self.parents(new[0])
        require(
            set(parents) <= {row["name"] for row in actual_parents},
            "axis lost an actual selected plane parent",
        )
        self.get(self.model, "ClearSelection2", True)
        return new[0]

    def create_plane(self, name, entries, arguments):
        before = {name for _, name, kind in self.top_features() if kind == "RefPlane"}
        self.select(entries)
        created = self.get(
            self.get(self.model, "FeatureManager"), "InsertRefPlane", *arguments
        )
        require(created is not None, "native constrained plane creation returned null")
        new = [
            value
            for value, name, kind in self.top_features()
            if kind == "RefPlane" and name not in before
        ]
        require(
            len(new) == 1, "plane command did not publish exactly one actual feature"
        )
        self.set(new[0], "Name", name)
        self.get(self.model, "ClearSelection2", True)
        return new[0]

    def plane_geometry(self, value):
        actual = self.declared_interface(
            self.get(value, "GetSpecificFeature2"), "IRefPlane"
        )
        transform = self.get(actual, "Transform")
        require(transform is not None, "actual plane has no transform")
        utility = self.get(self.app, "GetMathUtility")
        point = self.get(
            utility,
            "CreatePoint",
            self.sw.VARIANT(
                self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, [0.0, 0.0, 0.0]
            ),
        )
        vector = self.get(
            utility,
            "CreateVector",
            self.sw.VARIANT(
                self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, [0.0, 0.0, 1.0]
            ),
        )
        origin = [
            float(number)
            for number in self.get(
                self.get(point, "MultiplyTransform", transform), "ArrayData"
            )
        ]
        normal = [
            float(number)
            for number in self.get(
                self.get(vector, "MultiplyTransform", transform), "ArrayData"
            )
        ]
        norm = sqrt(sum(number * number for number in normal))
        require(norm > 0.0, "actual plane normal is zero")
        return {
            "origin_m": origin,
            "normal": [number / norm for number in normal],
            "transform": [float(number) for number in self.get(transform, "ArrayData")],
        }

    def axis_geometry(self, value):
        actual = self.declared_interface(
            self.get(value, "GetSpecificFeature2"), "IRefAxis"
        )
        return self.axis_object(actual)

    def axis_object(self, actual):
        values = [float(number) for number in self.get(actual, "GetRefAxisParams")]
        require(
            len(values) == 6,
            "reference axis must return its two actual endpoint triples",
        )
        delta = [values[index + 3] - values[index] for index in range(3)]
        norm = sqrt(sum(number * number for number in delta))
        require(norm > 1e-15, "reference axis has zero length")
        return {
            "endpoints_m": [values[:3], values[3:]],
            "unit": [number / norm for number in delta],
        }

    def check_line(self, label, observed, expected):
        dot = sum(a * b for a, b in zip(observed["unit"], expected))
        self.rec.close_number(label + " undirected alignment", abs(dot), 1.0)
        start = observed["endpoints_m"][0]
        projection = sum(a * b for a, b in zip(start, expected))
        for index in range(3):
            self.rec.close_number(
                label + " line through origin",
                start[index] - projection * expected[index],
                0.0,
            )

    def indexed(self, definition, name, index):
        (row,) = [
            row
            for row in self.api["interfaces"]["IRefPlaneFeatureData"]["members"]
            if row["names"][0] == name and row["invoke_kind"] == 2
        ]
        return self.rec.call(
            "indexed plane " + name,
            definition._oleobj_.Invoke,
            row["member_id"],
            0,
            2,
            True,
            index,
            parameters={
                "property": name,
                "index": index,
                "member_id": row["member_id"],
            },
        )

    def owned_dimension(self, name, kind, expected=None):
        owner = self.feature(name)
        parameter = self.get(self.model, "Parameter", "D1@" + name)
        require(parameter is not None, "actual driving dimension is absent: " + name)
        full = str(self.get(parameter, "FullName"))
        require(
            full.split("@")[:2] == ["D1", name],
            "parameter owner differs from the actual feature",
        )
        require(
            int(self.get(parameter, "DrivenState")) == 2
            and not bool(self.get(parameter, "ReadOnly")),
            "actual source dimension is not driving and editable",
        )
        value = float(self.get(parameter, "SystemValue"))
        rows, matches = [], []
        display = self.get(owner, "GetFirstDisplayDimension")
        while display is not None:
            require(
                len(rows) < 16, "owned display traversal exceeded the bounded profile"
            )
            linked = self.get(display, "GetDimension2", 0)
            require(linked is not None, "actual display lost its native dimension")
            target = str(self.get(linked, "FullName"))
            require(
                target not in {row["full_name"] for row in rows},
                "owned display traversal repeats",
            )
            row = {
                "full_name": target,
                "value_si": float(self.get(linked, "SystemValue")),
                "display_type": int(self.get(display, "Type2")),
            }
            rows.append(row)
            if target.split("@")[:2] == ["D1", name]:
                require(
                    row["display_type"] == self.api["enums"]["swDimensionType_e"][kind],
                    "wrong actual display physical dimension",
                )
                self.rec.close_number(
                    "owned display/named parameter", row["value_si"], value
                )
                matches.append(row)
            display = self.get(owner, "GetNextDisplayDimension", display)
        require(len(matches) == 1, "actual source parameter lacks one owned display")
        if expected is not None:
            self.rec.close_number("actual " + name + " driver", value, expected)
        return parameter, {
            "name": "D1@" + name,
            "full_name": full,
            "value_si": value,
            "driving": True,
            "editable": True,
            "dimension_type": kind,
            "owned_displays": rows,
        }

    def build(self, case, controller):
        self.model = self.rec.call(
            "new independent oblique source", controller.new_part
        )
        require(
            set(PRINCIPALS.values())
            <= {name for _, name, kind in self.top_features() if kind == "RefPlane"},
            "native template lacks expected principal planes",
        )
        self.create_axis(NAMES["hinge_a"], [PRINCIPALS["front"], PRINCIPALS["right"]])
        self.create_axis(NAMES["hinge_b"], [PRINCIPALS["front"], PRINCIPALS["top"]])
        self.create_plane(
            NAMES["angle_a"],
            [(PRINCIPALS["right"], 0), (NAMES["hinge_a"], 1)],
            angle_arguments(case["angle_a_rad"]),
        )
        self.create_plane(
            NAMES["angle_b"],
            [(PRINCIPALS["top"], 0), (NAMES["hinge_b"], 1)],
            angle_arguments(case["angle_b_rad"]),
        )
        self.create_axis(NAMES["direction"], [NAMES["angle_a"], NAMES["angle_b"]])
        self.create_plane(
            NAMES["limit"],
            [(PRINCIPALS["front"], 0)],
            [8, case["height_m"], 0, 0.0, 0, 0.0],
        )
        self.select([(PRINCIPALS["front"], 0)])
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        self.sketch = self.get(manager, "ActiveSketch")
        require(self.sketch is not None, "Front circle has no actual sketch owner")
        self.set(manager, "AddToDB", True)
        try:
            circle = self.get(
                manager, "CreateCircleByRadius", 0.0, 0.0, 0.0, case["radius_m"]
            )
            require(circle is not None, "solid circle profile creation failed")
        finally:
            self.set(manager, "AddToDB", False)
        self.segment_sources = {"entity-0": self.entity_binding(circle, "segment")}
        self.relation(
            17,
            [self.get(self.typed(circle, "SketchArc"), "GetCenterPoint2")],
            ["entity-0.center"],
        )
        self.dimension(
            circle,
            "curve-0",
            case["radius_m"],
            "radial",
            [case["radius_m"] * 1.7, case["radius_m"] * 1.3],
        )
        self.get(manager, "InsertSketch", True)
        sketch = self.created_sketch_feature()
        self.set(sketch, "Name", NAMES["sketch"])
        self.select(
            [(NAMES["sketch"], 0), (NAMES["limit"], 1), (NAMES["direction"], 16)]
        )
        boss = self.get(
            self.get(self.model, "FeatureManager"),
            "FeatureExtrusion3",
            *boss_arguments(case)
        )
        require(
            boss is not None, "selected-plane/selected-axis circular boss returned null"
        )
        self.set(boss, "Name", NAMES["boss"])
        require(
            bool(self.get(self.model, "ForceRebuild3", False)),
            "new oblique source rebuild failed",
        )

    def edit(self, case, index):
        key = EDITS[index]
        name = NAMES[
            {
                "angle_a_rad": "angle_a",
                "angle_b_rad": "angle_b",
                "radius_m": "sketch",
                "height_m": "limit",
            }[key]
        ]
        kind = (
            "swAngularDimension"
            if key.startswith("angle")
            else "swRadialDimension" if key == "radius_m" else "swLinearDimension"
        )
        parameter, _ = self.owned_dimension(name, kind)
        value = abs(case["edit_" + key])
        require(
            int(self.get(parameter, "SetSystemValue3", value, 1, self.sw.nothing()))
            == 0,
            "native owned source driver edit failed",
        )
        self.rec.close_number(
            "edited native driver", float(self.get(parameter, "SystemValue")), value
        )
        require(
            bool(self.get(self.model, "ForceRebuild3", False)),
            "oblique source failed after actual driver edit",
        )

    def snapshot(self, case, steps=0):
        wanted = self.predictions[str(steps)]
        result = {
            "expected_geometry": wanted,
            "planes": {},
            "axes": {},
            "dimensions": {},
            "parents": {},
        }
        self.rec.data["partial_oblique_snapshot"] = result
        self.rec.flush()
        for key in ("hinge_a", "hinge_b", "direction"):
            feature = self.feature(NAMES[key])
            result["axes"][key] = self.axis_geometry(feature)
            result["parents"][key] = self.parents(feature)
        for key in ("angle_a", "angle_b", "limit"):
            feature = self.feature(NAMES[key])
            result["planes"][key] = self.plane_geometry(feature)
            result["parents"][key] = self.parents(feature)
            definition = self.declared_interface(
                self.get(feature, "GetDefinition"), "IRefPlaneFeatureData"
            )
            require(
                bool(
                    self.get(
                        definition, "AccessSelections", self.model, self.sw.nothing()
                    )
                ),
                "plane source references are unavailable",
            )
            try:
                result["planes"][key]["public_type"] = int(self.get(definition, "Type"))
                result["planes"][key]["public_type2"] = int(
                    self.get(definition, "Type2")
                )
                slots = 1 if key == "limit" else 2
                result["planes"][key]["constraints"] = [
                    {
                        "index": index,
                        "constraint": int(
                            self.indexed(definition, "Constraint", index)
                        ),
                        "value_si": float(
                            self.indexed(definition, "AngleOrDistance", index)
                        ),
                        "has_reference": self.indexed(definition, "Reference", index)
                        is not None,
                    }
                    for index in range(slots)
                ]
            finally:
                self.get(definition, "ReleaseSelectionAccess")
            kind = "swLinearDimension" if key == "limit" else "swAngularDimension"
            expected = wanted["drivers"]["height_m" if key == "limit" else key + "_rad"]
            _, result["dimensions"][key] = self.owned_dimension(
                NAMES[key], kind, abs(expected)
            )
            self.rec.close_number(
                "actual plane definition angle or distance",
                result["planes"][key]["constraints"][0]["value_si"],
                abs(expected),
            )
        self.sketch = self.get(self.feature(NAMES["sketch"]), "GetSpecificFeature2")
        result["circle"] = circle_geometry(
            self, self.feature(NAMES["sketch"]), wanted["drivers"]["radius_m"]
        )
        _, result["dimensions"]["radius"] = self.owned_dimension(
            NAMES["sketch"], "swRadialDimension", wanted["drivers"]["radius_m"]
        )
        feature = self.feature(NAMES["boss"])
        result["parents"]["boss"] = self.parents(feature)
        definition = self.declared_interface(
            self.get(feature, "GetDefinition"), "IExtrudeFeatureData2"
        )
        require(
            bool(
                self.get(definition, "AccessSelections", self.model, self.sw.nothing())
            ),
            "extrusion references are unavailable",
        )
        try:
            result["extrusion"] = {
                "end_forward": int(self.get(definition, "GetEndCondition", True)),
                "end_reverse": int(self.get(definition, "GetEndCondition", False)),
                "both_directions": bool(self.get(definition, "BothDirections")),
                "reverse_direction": bool(self.get(definition, "ReverseDirection")),
                "thin": bool(self.get(definition, "IsThinFeature")),
                "draft_forward": bool(
                    self.get(definition, "GetDraftWhileExtruding", True)
                ),
                "draft_reverse": bool(
                    self.get(definition, "GetDraftWhileExtruding", False)
                ),
                "reported_forward_depth_m": float(
                    self.get(definition, "GetDepth", True)
                ),
            }
            direction = invoke(self, definition, "GetDirectionReference")
            require(
                isinstance(direction, tuple) and len(direction) == 5,
                "typed direction getter return shape differs from the frozen observer",
            )
            count, first, first_type, second, second_type = direction
            require(
                int(count) == 1 and first is not None and second is None,
                "extrusion lacks exactly one actual selected direction owner",
            )
            result["extrusion"]["direction_reference"] = {
                "count": int(count),
                "type1": int(first_type),
                "type2": int(second_type),
                "axis": self.axis_object(self.declared_interface(first, "IRefAxis")),
            }
            end = invoke(self, definition, "GetEndConditionReference", True)
            require(
                isinstance(end, tuple) and len(end) == 2 and end[0] is not None,
                "typed selected-end getter return shape differs",
            )
            end_transform = self.get(
                self.declared_interface(end[0], "IRefPlane"), "Transform"
            )
            result["extrusion"]["end_reference"] = {
                "reference_type": int(end[1]),
                "plane_transform": [
                    float(value) for value in self.get(end_transform, "ArrayData")
                ],
            }
            for observed, owned in zip(
                result["extrusion"]["end_reference"]["plane_transform"],
                result["planes"]["limit"]["transform"],
                strict=True,
            ):
                self.rec.close_number(
                    "selected end actual owned plane transform", observed, owned
                )
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        extension = self.get(self.model, "Extension")
        require(
            int(self.get(extension, "GetWhatsWrongCount")) == 0
            and int(self.get(extension, "NeedsRebuild2")) == 0,
            "native source has errors, warnings or pending rebuild",
        )
        bodies = list(
            self.get(
                self.declared_interface(self.model, "IPartDoc"), "GetBodies2", 0, True
            )
            or ()
        )
        result["body_count"] = len(bodies)
        result["mass"] = self.rec.call(
            "measure independent oblique solid", self.sw.mass, self.model
        )
        result["feature_tree"] = feature_tree(self, self.model)
        self.rec.flush()
        require(
            result["body_count"] == 1
            and result["mass"]
            and "error" not in result["mass"],
            "source lacks one measurable real solid",
        )
        require(
            all(
                row["error"] == 0
                and row["warning"] is False
                and row["suppressed"] is False
                for row in result["feature_tree"]
            ),
            "native source tree has a failed, warned or suppressed owner",
        )
        for name, expected in (
            ("volume", wanted["volume_m3"]),
            ("area", wanted["area_m2"]),
        ):
            self.rec.close_number(
                "independent oblique " + name, result["mass"][name], expected
            )
        for index in range(3):
            self.rec.close_number(
                "independent oblique COM",
                result["mass"]["com"][index],
                wanted["com_m"][index],
            )
        self.check_line("actual hinge A", result["axes"]["hinge_a"], [0.0, 1.0, 0.0])
        self.check_line("actual hinge B", result["axes"]["hinge_b"], [-1.0, 0.0, 0.0])
        self.check_line(
            "actual direction axis",
            result["axes"]["direction"],
            wanted["axis_unit_positive_z"],
        )
        self.check_line(
            "actual extrusion direction owner",
            result["extrusion"]["direction_reference"]["axis"],
            wanted["axis_unit_positive_z"],
        )
        for key in ("angle_a", "angle_b"):
            actual = result["planes"][key]
            normal = wanted["angle_plane_normals"][key]
            self.rec.close_number(
                "actual angular plane normal",
                abs(sum(a * b for a, b in zip(actual["normal"], normal))),
                1.0,
            )
            self.rec.close_number(
                "actual angular plane through origin",
                sum(a * b for a, b in zip(actual["origin_m"], normal)),
                0.0,
            )
            constraints = actual["constraints"]
            require(
                [row["constraint"] & 255 for row in constraints] == [16, 4]
                and all(row["has_reference"] for row in constraints),
                "actual angle/line constraints differ",
            )
        self.rec.close_number(
            "actual height plane position",
            result["planes"]["limit"]["origin_m"][2],
            wanted["drivers"]["height_m"],
        )
        require(
            result["extrusion"]["end_forward"] == 4
            and not any(
                result["extrusion"][key]
                for key in (
                    "both_directions",
                    "reverse_direction",
                    "thin",
                    "draft_forward",
                    "draft_reverse",
                )
            ),
            "actual extrusion flags or selected end differ",
        )
        require(
            NAMES["sketch"] in {row["name"] for row in result["parents"]["boss"]},
            "extrusion lost its actual profile parent",
        )
        result["passed"] = True
        self.rec.data.pop("partial_oblique_snapshot", None)
        self.rec.flush()
        return result
