import math
from pathlib import Path

import Swapp
from AuthorBlindCutSources import BlindCutAuthor
from AuthorCurves import digest
from FilletApi import FLAGS
from FilletModel import predict, require

SKETCH, BOSS, FILLET = "FilletStockSketch", "FilletStockBoss", "ConstantEdgeFillet"
MARK = 1
LENGTH_EPSILON = 1e-9


def equal_point(actual, expected):
    return len(actual) == len(expected) == 3 and all(
        abs(a - b) <= LENGTH_EPSILON for a, b in zip(actual, expected, strict=True)
    )


def same_points(actual, expected, label):
    require(len(actual) == len(expected), f"{label}: unexpected point count")
    todo = list(actual)
    for point in expected:
        indexes = [index for index, item in enumerate(todo) if equal_point(item, point)]
        require(len(indexes) == 1, f"{label}: expected exactly one match for {point}")
        todo.pop(indexes[0])


class FilletAuthor(BlindCutAuthor):
    def __init__(self, app, recorder, constants):
        super().__init__(app, recorder, Swapp)
        self.constants = constants

    def transform(self, coordinates, frame, *, vector=False):
        utility = self.get(self.app, "GetMathUtility")
        values = Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8, tuple(coordinates))
        kind = "CreateVector" if vector else "CreatePoint"
        result = self.get(utility, kind, values)
        return [float(value) for value in self.get(self.get(result, "MultiplyTransform", frame), "ArrayData")]

    def same(self, actual, expected):
        return int(self.get(self.app, "IsSame", actual, expected)) == self.constants["swObjectSame"]

    def reference(self, value):
        raw = self.get(self.get(self.model, "Extension"), "GetPersistReference3", value)
        require(raw is not None and 0 < len(raw) <= 4096, "missing bounded native persistent reference")
        return bytes(raw).hex()

    def one_body(self):
        bodies = tuple(self.get(self.model, "GetBodies2", self.constants["swSolidBody"], False) or ())
        require(len(bodies) == 1 and not self.get(self.model, "GetBodies2", self.constants["swSheetBody"], False),
                "the source requires one actual solid and no sheet bodies")
        return self.typed(bodies[0], "Body2")

    def profile(self, case):
        width, height, _ = case["size_mm"]
        return {"kind": "rectangle", "center_mm": case["center_mm"], "width_mm": width, "height_mm": height}

    def author(self, case, session):
        template = Path(self.rec.call("locate installed default part template", session.template, "part"))
        require(template.is_absolute() and template.is_file(), "default native part template is unavailable")
        self.rec.data["part_template_sha256"] = digest(template)
        self.model = self.rec.call("new blank native part", session.new_part)
        require(digest(template) == self.rec.data["part_template_sha256"], "native part template changed")
        analytical = predict(case)
        (left, right), (low, high), _ = analytical["stock_bounds"]
        self.create_sketch("front", SKETCH, "CreateCornerRectangle", (left, low, 0.0, right, high, 0.0))
        manager = self.get(self.model, "FeatureManager")
        blind = self.constants["swEndCondBlind"]
        args = (True, False, False, blind, blind, case["size_mm"][2] / 1000, 0.0, False,
                False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        boss = self.get(manager, "FeatureExtrusion3", *args)
        require(boss is not None, "native blind stock creation failed")
        self.set(boss, "Name", BOSS)
        self.clean_rebuild()
        profile, inverse = self.inspect_profile(SKETCH, self.profile(case))
        stock = self.measure_body(analytical, inverse, "unfilleted")
        stock["profile"] = profile
        self.rec.data["unfilleted"] = stock
        self.rec.flush()
        endpoints = [self.transform(point, inverse) for point in analytical["source_edge"]]
        edge, proof = self.find_edge(endpoints, boss)
        self.create_fillet(manager, edge, proof, case["radius_mm"] / 1000)

    def edge_points(self, edge):
        pair = [self.get(edge, name) for name in ("GetStartVertex", "GetEndVertex")]
        require(all(vertex is not None for vertex in pair), "stock edge lost its two endpoints")
        return [[float(value) for value in self.get(vertex, "GetPoint")] for vertex in pair]

    def find_edge(self, endpoints, boss):
        body = self.one_body()
        edges = tuple(self.typed(edge, "Edge") for edge in self.get(body, "GetEdges") or ())
        require(len(edges) == 12, "fillet input is not the actual unrounded box topology")
        matches = []
        for edge in edges:
            pair = self.edge_points(edge)
            if any(all(equal_point(a, b) for a, b in zip(pair, order, strict=True))
                   for order in (endpoints, endpoints[::-1])):
                matches.append((edge, pair))
        require(len(matches) == 1, "authored endpoint pair must identify exactly one stock edge")
        edge, pair = matches[0]
        require(bool(self.get(self.get(edge, "GetCurve"), "IsLine")), "matched native edge is not straight")
        faces = tuple(self.typed(face, "Face2") for face in self.get(edge, "GetTwoAdjacentFaces2") or ())
        require(len(faces) == 2 and all(bool(self.get(self.get(face, "GetSurface"), "IsPlane"))
                and self.same(self.get(face, "GetBody"), body) and self.same(self.get(face, "GetFeature"), boss)
                for face in faces), "edge must bind the two actual planar supports of the stock boss")
        return edge, {"endpoints_m": pair, "edge_reference": self.reference(edge),
                      "stock_boss_reference": self.reference(boss),
                      "adjacent_face_references": [self.reference(face) for face in faces]}

    def create_fillet(self, manager, edge, proof, radius):
        self.get(self.model, "ClearSelection2", True)
        definition = self.typed(self.get(manager, "CreateDefinition", self.constants["swFmFillet"]),
                                "SimpleFilletFeatureData2")
        require(bool(self.get(definition, "Initialize", self.constants["swConstRadiusFillet"])),
                "native simple fillet did not initialize as constant radius")
        self.set(definition, "ConicTypeForCrossSectionProfile", self.constants["swFeatureFilletCircular"])
        self.set(definition, "PropagateToTangentFaces", False)
        self.set(definition, "IsMultipleRadius", False)
        self.set(definition, "AsymmetricFillet", False)
        self.set(definition, "DefaultRadius", radius)
        selection = self.get(self.model, "SelectionManager")
        select_data = self.get(selection, "CreateSelectData")
        self.set(select_data, "Mark", MARK)
        require(bool(self.get(self.typed(edge, "Entity"), "Select4", False, select_data)),
                "actual stock edge could not be marked for the constant fillet")
        require(all(int(self.get(selection, "GetSelectedObjectCount2", mark)) == 1 for mark in (-1, MARK))
                and self.get(selection, "GetSelectedObjectType3", 1, MARK) == self.constants["swSelEDGES"]
                and self.same(self.get(selection, "GetSelectedObject6", 1, MARK), edge),
                "marked selection did not retain the actual resolved edge")
        array = Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_DISPATCH, (edge,))
        self.rec.call("set Edges", setattr, definition, "Edges", array,
                      parameters={"variant": "SAFEARRAY(IDispatch)", "edge": proof})
        self.rec.data["authored_edge"] = proof
        self.rec.flush()
        self.confirm_modes(definition, radius)
        self.confirm_edge(definition, edge)
        feature = self.get(manager, "CreateFeature", definition)
        require(feature is not None, "native CreateFeature returned no constant edge fillet")
        self.set(feature, "Name", FILLET)
        self.get(self.model, "ClearSelection2", True)

    def confirm_modes(self, definition, radius):
        fields = {key: self.get(definition, key) for key in ("Type", "ConicTypeForCrossSectionProfile",
                  "DefaultRadius", *FLAGS)}
        self.rec.data["last_fillet_definition"] = fields
        self.rec.flush()
        require(fields["Type"] == self.constants["swConstRadiusFillet"]
                and fields["ConicTypeForCrossSectionProfile"] == self.constants["swFeatureFilletCircular"]
                and not any(fields[key] for key in FLAGS), "native definition left the ordinary symmetric circular scope")
        self.rec.close_number("actual default radius", fields["DefaultRadius"], radius)
        return fields

    def confirm_edge(self, definition, edge):
        edges = tuple(self.get(definition, "Edges") or ())
        require(len(edges) == int(self.get(definition, "GetEdgeCount")) == 1 and self.same(edges[0], edge),
                "native fillet definition lost its exact selected stock edge")

    def read_definition(self, feature, boss, endpoints, radius):
        definition = self.typed(self.get(feature, "GetDefinition"), "SimpleFilletFeatureData2")
        require(bool(self.get(definition, "AccessSelections", self.model, Swapp.nothing())),
                "native fillet selection could not roll back to its actual source")
        try:
            fields = self.confirm_modes(definition, radius)
            edge, proof = self.find_edge(endpoints, boss)
            self.confirm_edge(definition, edge)
            require(not self.get(definition, "Features") and not self.get(definition, "Loops")
                    and int(self.get(definition, "FilletItemsCount")) == 1
                    and self.same(self.get(definition, "GetFilletItemAtIndex", 0), edge),
                    "native fillet has an alternate input selection or fillet item")
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        parents = [str(self.get(parent, "Name")) for parent in self.get(feature, "GetParents") or ()]
        require(BOSS in parents, "native fillet lost its actual stock dependency")
        return {"properties": fields, "inputs": proof, "parents": parents,
                "type": str(self.get(feature, "GetTypeName2")), "legacy_type": str(self.get(feature, "GetTypeName")),
                "feature_reference": self.reference(feature)}

    def driver(self, feature, radius):
        preference = self.constants["swDisplayFeatureDimensions"]
        old = bool(self.get(self.model, "GetUserPreferenceToggle", preference))
        try:
            self.get(self.model, "SetUserPreferenceToggle", preference, True)
            require(bool(self.get(self.model, "GetUserPreferenceToggle", preference)), "cannot expose actual feature dimensions")
            display = self.get(feature, "GetFirstDisplayDimension")
            inventory, driving = [], []
            while display is not None:
                require(len(inventory) < 16, "fillet dimension inventory exceeded its bound")
                dimension = self.typed(self.get(display, "GetDimension2", 0), "Dimension")
                name = str(self.get(dimension, "FullName"))
                value = float(self.get(dimension, "SystemValue"))
                state = int(self.get(dimension, "DrivenState"))
                readonly = bool(self.get(dimension, "ReadOnly"))
                row = {"name": name, "value_si": value, "kind": int(self.get(display, "Type2")),
                       "driven_state": state, "read_only": readonly}
                inventory.append(row)
                if state == self.constants["swDimensionDriving"] and not readonly:
                    driving.append((row, dimension))
                display = self.get(feature, "GetNextDisplayDimension", display)
        finally:
            self.get(self.model, "SetUserPreferenceToggle", preference, old)
            require(bool(self.get(self.model, "GetUserPreferenceToggle", preference)) == old,
                    "native fillet observation could not restore its display preference")
        self.rec.data["last_dimensions"] = inventory
        self.rec.flush()
        require(len(driving) == 1, "the native fillet requires exactly one live radius driver")
        row, dimension = driving[0]
        require(row["name"].split("@")[1:2] == [FILLET] and row["kind"] == self.constants["swRadialDimension"],
                "the live radius driver does not belong to this fillet")
        self.rec.close_number("native editable radius", row["value_si"], radius)
        return row, dimension

    def clean_rebuild(self):
        require(bool(self.get(self.model, "ForceRebuild3", False)), "ordinary fillet document rebuild failed")
        require(int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0,
                "ordinary fillet document has rebuild errors or warnings")

    def topology(self, body, analytical, inverse, feature):
        faces = tuple(self.typed(face, "Face2") for face in self.get(body, "GetFaces") or ())
        vertices = [[float(value) for value in self.get(vertex, "GetPoint")]
                    for vertex in self.get(body, "GetVertices") or ()]
        counts = {"faces": len(faces), "edges": len(self.get(body, "GetEdges") or ()), "vertices": len(vertices)}
        require(counts == analytical["counts"], "native fillet solid does not match predicted counts")
        expected = [self.transform(point, inverse) for point in analytical["vertices"]]
        same_points(vertices, expected, "corner and tangent vertex ownership")
        result = {"counts": counts, "vertices_m": vertices}
        if feature is not None:
            result["cylinder"] = self.cylinder(faces, analytical, inverse, feature)
        return result

    def cylinder(self, faces, analytical, inverse, feature):
        cylinders = []
        for face in faces:
            surface = self.get(face, "GetSurface")
            if bool(self.get(surface, "IsCylinder")):
                cylinders.append((face, surface))
            else:
                require(bool(self.get(surface, "IsPlane")), "native fillet has an unexpected surface kind")
        require(len(cylinders) == 1, "native simple fillet must create exactly one cylindrical face")
        face, surface = cylinders[0]
        require(self.same(self.get(face, "GetFeature"), feature)
                and any(self.same(face, member) for member in self.get(feature, "GetFaces") or ()),
                "cylindrical face is not the actual output of the measured fillet feature")
        values = [float(value) for value in self.get(surface, "CylinderParams")]
        require(len(values) == 7 and all(math.isfinite(value) for value in values), "invalid native cylinder values")
        origin = self.transform(analytical["fillet_axis_origin"], inverse)
        axis = self.transform([int(i == analytical["edge_axis"]) for i in range(3)], inverse, vector=True)
        delta = [a - b for a, b in zip(values[:3], origin, strict=True)]
        shift = sum(a * b for a, b in zip(delta, axis, strict=True))
        self.rec.close_number("fillet output cylinder axis", abs(sum(a * b for a, b in zip(values[3:6], axis, strict=True))), 1.0)
        self.rec.close_number("fillet output cylinder radius", values[6], analytical["radius_m"])
        for index in range(3):
            self.rec.close_number(f"fillet output cylinder line component {index}", delta[index], shift * axis[index], absolute=1e-10)
        return {"params": values, "face": self.reference(face)}

    def extrema(self, body, analytical, inverse, label):
        corners = [self.transform(point, inverse) for point in predict_bounds(analytical)]
        results = []
        for sign in (-1.0, 1.0):
            for axis in range(3):
                direction = [sign if index == axis else 0.0 for index in range(3)]
                result = [Swapp.VARIANT(Swapp.pythoncom.VT_BYREF | Swapp.pythoncom.VT_R8, 0.0) for _ in range(3)]
                require(bool(self.get(body, "GetExtremePoint", *direction, *result)), "exact body extrema query failed")
                coordinate = float(result[axis].value)
                target = (min if sign < 0 else max)(point[axis] for point in corners)
                self.rec.close_number(f"{label} exact extrema {sign} {axis}", coordinate, target, absolute=1e-10)
                results.append(coordinate)
        return results

    def measure_body(self, analytical, inverse, label, feature=None):
        body = self.one_body()
        result = self.topology(body, analytical, inverse, feature)
        mass = self.rec.call("actual solid mass properties", Swapp.mass, self.model)
        require(mass is not None and "error" not in mass, "ordinary source solid has no measurable mass properties")
        numeric = {"volume": analytical["volume"], "area": analytical["area"],
                   "com": self.transform(analytical["com"], inverse)}
        self.close_six(label + " volume", mass["volume"], numeric["volume"], 1e-21)
        self.close_six(label + " area", mass["area"], numeric["area"], 1e-16)
        for index, (a, b) in enumerate(zip(mass["com"], numeric["com"], strict=True)):
            self.close_six(f"{label} centre of mass {index}", a, b, 1e-10)
        return result | {"bodies": 1, "native": mass, "expected": numeric,
                         "bounds_m": self.extrema(body, analytical, inverse, label),
                         "source_edge_m": [self.transform(p, inverse) for p in analytical["source_edge"]]}

    def close_six(self, label, actual, expected, near_zero):
        significant = (abs(actual - expected) <= near_zero if abs(expected) < near_zero
                       else float(f"{actual:.6g}") == float(f"{expected:.6g}"))
        self.rec.data["checks"].append({"name": label, "actual": actual, "expected": expected,
                                         "method": "six_significant_figures_or_near_zero", "passed": significant})
        self.rec.flush()
        require(significant, f"{label}: native result differs at six significant figures")

    def snapshot(self, case, label, radius):
        self.clean_rebuild()
        tree = self.feature_tree(required_names=(SKETCH, BOSS, FILLET))
        names = [row["name"] for row in tree]
        require(names.index(BOSS) < names.index(FILLET), "native tree reordered the fillet before its stock")
        stock = self.inspect_feature(BOSS, SKETCH, case["size_mm"][2], True)
        require(not stock["reverse"], "native stock reversed its authored depth")
        profile, inverse = self.inspect_profile(SKETCH, self.profile(case))
        analytic = predict(case, radius)
        boss, fillet = (self.get(self.model, "FeatureByName", name) for name in (BOSS, FILLET))
        edge = [self.transform(point, inverse) for point in analytic["source_edge"]]
        definition = self.read_definition(fillet, boss, edge, radius)
        body = self.measure_body(analytic, inverse, label, fillet)
        driver, _ = self.driver(fillet, radius)
        result = {"tree": tree, "stock": stock, "profile": profile, "definition": definition,
                  "driver": driver, "body": body}
        self.rec.data[label] = result
        self.rec.flush()
        return result

    def edit_radius(self, initial, target):
        feature = self.get(self.model, "FeatureByName", FILLET)
        prior, dimension = self.driver(feature, initial)
        status = int(self.get(dimension, "SetSystemValue3", target,
                              self.constants["swSetValue_InThisConfiguration"], Swapp.nothing()))
        require(status == self.constants["swSetValue_Successful"], f"live fillet radius edit failed with status {status}")
        self.rec.close_number("requested live radius after setter", self.get(dimension, "SystemValue"), target)
        self.rec.data["edit"] = {"driver": prior, "requested_m": target, "setter_status": status}
        self.rec.flush()


def predict_bounds(analytical):
    from itertools import product

    return product(*analytical["stock_bounds"])
