from __future__ import annotations

from math import isclose

from AuthorCurves import CurveAuthor, require
from ThroughAllSourcePlan import NAMES, PLANES, geometry, model_point, validate


class ThroughAllAuthor(CurveAuthor):
    def feature(self, name):
        part = self.typed(self.model, "PartDoc")
        result = self.get(part, "FeatureByName", name)
        require(result is not None, f"missing actual named feature {name}")
        return result

    def create_profile(self, case, name, method, values):
        self.get(self.model, "ClearSelection2", True)
        extension = self.get(self.model, "Extension")
        require(
            self.get(
                extension,
                "SelectByID2",
                PLANES[case["plane"]],
                "PLANE",
                0.0,
                0.0,
                0.0,
                False,
                0,
                self.sw.nothing(),
                0,
            ),
            "principal-plane selection failed",
        )
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        require(
            self.get(manager, "ActiveSketch") is not None, "no active source sketch"
        )
        self.set(manager, "AddToDB", True)
        try:
            created = self.get(manager, method, *values)
            require(
                created is not None
                and (method != "CreateCornerRectangle" or len(created) == 4),
                "profile primitive creation failed",
            )
        finally:
            self.set(manager, "AddToDB", False)
        self.get(manager, "InsertSketch", True)
        feature = self.get(self.model, "FeatureByPositionReverse", 0)
        require(
            feature is not None
            and self.get(feature, "GetTypeName2") == "ProfileFeature",
            "latest source feature is not the created profile",
        )
        self.set(feature, "Name", name)
        self.get(self.model, "ClearSelection2", True)
        require(
            self.get(feature, "Select2", False, 0), "authored profile selection failed"
        )
        selected = self.get(self.model, "SelectionManager")
        require(
            int(self.get(selected, "GetSelectedObjectCount2", -1))
            == int(self.get(selected, "GetSelectedObjectCount2", 0))
            == 1,
            "profile selection contains additional owners",
        )

    def build(self, case, controller):
        validate(case)
        self.model = self.rec.call(
            "create native through-all source part", controller.new_part
        )
        width, height, depth = case["stock_size_m"]
        cx, cy = case["stock_center_m"]
        self.create_profile(
            case,
            NAMES[0],
            "CreateCornerRectangle",
            (
                cx - width / 2,
                cy - height / 2,
                0.0,
                cx + width / 2,
                cy + height / 2,
                0.0,
            ),
        )
        manager = self.get(self.model, "FeatureManager")
        stock_args = (
            True,
            False,
            False,
            6,
            0,
            depth,
            0.0,
            False,
            False,
            False,
            False,
            0.0,
            0.0,
            False,
            False,
            False,
            False,
            True,
            True,
            True,
            0,
            0.0,
            False,
        )
        feature = self.get(manager, "FeatureExtrusion3", *stock_args)
        require(feature is not None, "native mid-plane stock creation failed")
        self.set(feature, "Name", NAMES[1])
        cx, cy = case["circle_center_m"]
        self.create_profile(
            case, NAMES[2], "CreateCircleByRadius", (cx, cy, 0.0, case["radius_m"])
        )
        both = case["direction"] == "both"
        reverse = case["direction"] == "reverse"
        d1, d2 = case["api_placeholder_depths_m"]
        common = (
            not both,
            False,
            (not reverse if case["operation"] == "cut" else reverse),
            1,
            1 if both else 0,
            d1,
            d2,
            False,
            False,
            False,
            False,
            0.0,
            0.0,
            False,
            False,
            False,
            False,
        )
        if case["operation"] == "cut":
            arguments = (
                *common,
                False,
                True,
                True,
                False,
                False,
                False,
                0,
                0.0,
                False,
                False,
            )
            feature = self.get(manager, "FeatureCut4", *arguments)
        else:
            arguments = (*common, True, True, True, 0, 0.0, False)
            feature = self.get(manager, "FeatureExtrusion3", *arguments)
        require(feature is not None, "native through-all operation returned no feature")
        self.set(feature, "Name", NAMES[3])
        self.rec.data["source_authoring"] = {
            "stock_method": "FeatureExtrusion3",
            "stock_arguments": list(stock_args),
            "method": (
                "FeatureCut4" if case["operation"] == "cut" else "FeatureExtrusion3"
            ),
            "arguments": list(arguments),
            "through_all_both_encoding": (
                "two native type-1 directions"
                if both
                else "single native type-1 direction"
            ),
            "api_enum_9_exercised": False,
        }
        self.rec.flush()

    def owned_dimensions(self, name):
        feature = self.feature(name)
        display = self.get(feature, "GetFirstDisplayDimension")
        result, seen = [], set()
        while display is not None:
            require(len(result) < 64, "feature display traversal exceeded its bound")
            dimension = self.get(display, "GetDimension2", 0)
            require(dimension is not None, "actual feature display has no dimension")
            full = str(self.get(dimension, "FullName"))
            require(
                full not in seen and full.split("@")[1:2] == [name],
                "dimension ownership is stale or repeated",
            )
            seen.add(full)
            result.append(
                {
                    "name": full,
                    "value_m": float(self.get(dimension, "SystemValue")),
                    "read_only": bool(self.get(dimension, "ReadOnly")),
                    "driven_state": int(self.get(dimension, "DrivenState")),
                }
            )
            display = self.get(feature, "GetNextDisplayDimension", display)
        return result

    def definition(self, name):
        feature = self.feature(name)
        data = self.typed(self.get(feature, "GetDefinition"), "ExtrudeFeatureData2")
        observed = {
            "type": str(self.get(feature, "GetTypeName2")),
            "fallback_type": str(self.get(feature, "GetTypeName")),
            "end_forward": int(self.get(data, "GetEndCondition", True)),
            "end_reverse": int(self.get(data, "GetEndCondition", False)),
            "depth_forward_m": float(self.get(data, "GetDepth", True)),
            "depth_reverse_m": float(self.get(data, "GetDepth", False)),
            "both_directions": bool(self.get(data, "BothDirections")),
            "reverse_direction": bool(self.get(data, "ReverseDirection")),
            "from_type": int(self.get(data, "FromType")),
            "thin": bool(self.get(data, "IsThinFeature")),
            "draft_forward": bool(self.get(data, "GetDraftWhileExtruding", True)),
            "draft_reverse": bool(self.get(data, "GetDraftWhileExtruding", False)),
            "dimensions": self.owned_dimensions(name),
            "parents": [
                str(self.get(parent, "Name"))
                for parent in self.get(feature, "GetParents") or ()
            ],
        }
        if name == NAMES[3] and observed["fallback_type"] == "Cut":
            observed.update(
                flip_side_to_cut=bool(self.get(data, "FlipSideToCut")),
                normal_cut=bool(self.get(data, "NormalCut")),
            )
        return observed

    def profiles(self, case):
        result = {}
        width, height, _ = case["stock_size_m"]
        cx, cy = case["stock_center_m"]
        expected = (
            {
                "kind": "rectangle",
                "center_mm": [1000 * cx, 1000 * cy],
                "width_mm": 1000 * width,
                "height_mm": 1000 * height,
            },
            {
                "kind": "circle",
                "center_mm": [1000 * item for item in case["circle_center_m"]],
                "radius_mm": 1000 * case["radius_m"],
            },
        )
        for name, request in zip((NAMES[0], NAMES[2]), expected, strict=True):
            self.sketch = self.get(self.feature(name), "GetSpecificFeature2")
            require(self.sketch is not None, "native profile has no actual sketch")
            actual = self.geometry()
            self.check_geometry({"profile": request}, actual)
            transform = self.get(
                self.get(self.sketch, "ModelToSketchTransform"), "Inverse"
            )
            values = list(self.get(transform, "ArrayData"))
            require(len(values) >= 13, "sketch frame is incomplete")
            for local in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)):
                point = [
                    sum(local[row] * values[row * 3 + col] for row in range(3))
                    * values[12]
                    + values[9 + col]
                    for col in range(3)
                ]
                require(
                    all(
                        isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
                        for a, b in zip(
                            point, model_point(case["plane"], local), strict=True
                        )
                    ),
                    "the actual sketch frame differs from the independent principal-plane rule",
                )
            result[name] = {"geometry": actual, "sketch_to_model": values}
        return result

    def snapshot(self, case, edited=False, rebuild=True):
        if rebuild:
            require(
                bool(self.get(self.model, "ForceRebuild3", False)),
                "native through-all rebuild failed",
            )
        require(
            int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0,
            "native through-all document contains errors or warnings",
        )
        tree = self.feature_tree(required_names=NAMES)
        stock, operation = self.definition(NAMES[1]), self.definition(NAMES[3])
        require(
            stock["fallback_type"] in ("Extrusion", "BaseBody", "Boss")
            and operation["fallback_type"]
            in (
                ("Cut",)
                if case["operation"] == "cut"
                else ("Extrusion", "BaseBody", "Boss")
            ),
            "native operation family differs from the authored cut or boss",
        )
        require(
            stock["end_forward"] == 6
            and not stock["both_directions"]
            and not stock["thin"],
            "native stock lost its mid-plane termination",
        )
        target = case["edit_stock_depth_m"] if edited else case["stock_size_m"][2]
        self.rec.close_number(
            "actual stock driving depth", stock["depth_forward_m"], target
        )
        both = case["direction"] == "both"
        require(
            operation["end_forward"] == 1
            and operation["both_directions"] == both
            and (not both or operation["end_reverse"] == 1),
            "native through-all end-condition or direction count differs",
        )
        require(
            operation["from_type"] == 0
            and not any(
                operation[key] for key in ("thin", "draft_forward", "draft_reverse")
            ),
            "native through-all operation acquired additional termination state",
        )
        require(
            operation["reverse_direction"]
            == (
                (case["direction"] != "reverse")
                if case["operation"] == "cut"
                else (case["direction"] == "reverse")
            ),
            "native operation reversal differs from the exact author argument",
        )
        if case["operation"] == "cut":
            require(
                not operation["flip_side_to_cut"] and not operation["normal_cut"],
                "native through-all cut changed removal scope",
            )
        require(
            not any(
                not row["read_only"] and row["driven_state"] == 2
                for row in operation["dimensions"]
            ),
            "native through-all operation still owns an active driving dimension",
        )
        profiles = self.profiles(case)
        mass = self.rec.call(
            "measure native through-all mass properties", self.sw.mass, self.model
        )
        bodies = self.rec.call(
            "measure native through-all solid bodies", self.sw.bodies, self.model
        )
        require(
            bodies == 1 and mass is not None and "error" not in mass,
            "through-all source has no single measurable solid",
        )
        prediction = geometry(case, edited)
        if prediction["analytic_qualified"]:
            self.rec.close_number(
                "through-all analytic volume",
                mass["volume"],
                prediction["volume"],
                absolute=1e-22,
            )
            self.rec.close_number(
                "through-all analytic area",
                mass["area"],
                prediction["area"],
                absolute=1e-18,
            )
            for axis, (actual, expected) in enumerate(
                zip(mass["com"], prediction["com"], strict=True)
            ):
                self.rec.close_number(
                    f"through-all analytic centroid {axis}",
                    actual,
                    expected,
                    absolute=1e-10,
                )
        else:
            require(
                mass["volume"] > prediction["minimum_volume"] and mass["area"] > 0,
                "through-all boss made no positive external material",
            )
        return {
            "tree": tree,
            "stock": stock,
            "operation": operation,
            "profiles": profiles,
            "mass": mass,
            "bodies": bodies,
            "prediction": prediction,
            "analytic_geometry_qualified": prediction["analytic_qualified"],
            "edited": edited,
        }

    def edit_stock(self, case):
        dimension = self.get(self.model, "Parameter", "D1@" + NAMES[1])
        require(
            dimension is not None
            and str(self.get(dimension, "FullName")).split("@")[1:2] == [NAMES[1]],
            "stock driving owner is missing",
        )
        require(
            not self.get(dimension, "ReadOnly")
            and int(self.get(dimension, "DrivenState")) == 2,
            "stock dimension is not driving and editable",
        )
        self.rec.close_number(
            "stock initial parameter",
            self.get(dimension, "SystemValue"),
            case["stock_size_m"][2],
        )
        require(
            int(
                self.get(
                    dimension,
                    "SetSystemValue3",
                    case["edit_stock_depth_m"],
                    1,
                    self.sw.nothing(),
                )
            )
            == 0,
            "stock depth setter failed",
        )
        self.rec.close_number(
            "stock changed parameter",
            self.get(dimension, "SystemValue"),
            case["edit_stock_depth_m"],
        )
