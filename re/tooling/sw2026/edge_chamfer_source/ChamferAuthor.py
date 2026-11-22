import math
import re
from pathlib import Path

import Swapp
from AuthorCurves import digest
from FilletAuthor import FilletAuthor, equal_point, same_points
from FilletModel import require

from ChamferModel import ROLES, compare_six, values_si

SKETCH, BOSS, CHAMFER = "ChamferStockSketch", "ChamferStockBoss", "DistanceAngleEdgeChamfer"
EDGE_MARK = 1


class ChamferAuthor(FilletAuthor):
    feature_name = CHAMFER

    def author(self, case, session, stock):
        manager, edge, proof = self.author_stock(case, session, stock)
        self.create_chamfer(manager, edge, proof, self.profile_params(case, False))

    def profile_params(self, case, edited):
        return values_si(case, edited)

    def author_stock(self, case, session, stock):
        template = Path(self.rec.call("locate installed default part template", session.template, "part"))
        require(template.is_absolute() and template.is_file(), "installed part template is unavailable")
        self.rec.data["part_template_sha256"] = self.rec.call("hash part template", digest, template)
        self.model = self.rec.call("new blank native part", session.new_part)
        require(digest(template) == self.rec.data["part_template_sha256"], "installed part template changed")
        (left, right), (low, high), _ = stock["stock_bounds"]
        self.create_sketch("front", SKETCH, "CreateCornerRectangle", (left, low, 0.0, right, high, 0.0))
        manager = self.get(self.model, "FeatureManager")
        blind = self.constants["swEndCondBlind"]
        boss = self.get(manager, "FeatureExtrusion3", True, False, False, blind, blind, case["size_mm"][2] / 1000,
                        0.0, False, False, False, False, 0.0, 0.0, False, False, False, False,
                        True, True, True, 0, 0.0, False)
        require(boss is not None, "native blind box creation failed")
        self.set(boss, "Name", BOSS)
        self.clean_rebuild()
        profile, inverse = self.inspect_profile(SKETCH, self.profile(case))
        self.rec.data["unbeveled"] = self.measure_body(stock, inverse, "unbeveled") | {"profile": profile}
        self.check_face_areas(self.one_body(), stock, "unbeveled")
        endpoints = [self.transform(point, inverse) for point in stock["source_edge"]]
        edge, proof = self.find_edge(endpoints, boss)
        return manager, edge, proof

    def select_chamfer(self, edge, proof):
        self.get(self.model, "ClearSelection2", True)
        selection = self.get(self.model, "SelectionManager")
        data = self.get(selection, "CreateSelectData")
        self.set(data, "Mark", EDGE_MARK)
        require(bool(self.get(self.typed(edge, "Entity"), "Select4", False, data)), "cannot select the actual stock edge")
        counts = [int(self.get(selection, "GetSelectedObjectCount2", mark)) for mark in (-1, EDGE_MARK)]
        kind = int(self.get(selection, "GetSelectedObjectType3", 1, EDGE_MARK))
        selected = self.get(selection, "GetSelectedObject6", 1, EDGE_MARK)
        require(counts == [1, 1] and kind == self.constants["swSelEDGES"] and selected is not None
                and self.same(self.typed(selected, "Edge"), edge), "selection did not retain the one marked stock edge")
        self.rec.data["authored_edge"] = proof | {"mark": EDGE_MARK, "counts": counts, "selection_kind": kind}
        self.rec.flush()

    def create_chamfer(self, manager, edge, proof, params):
        self.select_chamfer(edge, proof)
        feature = self.get(manager, "InsertFeatureChamfer", 0, self.constants["swChamferAngleDistance"],
                           *params, 0.0, 0.0, 0.0, 0.0)
        require(feature is not None, "InsertFeatureChamfer returned no feature for the exact edge")
        self.set(feature, "Name", self.feature_name)
        self.get(self.model, "ClearSelection2", True)

    def definition(self, feature, boss, endpoints, params):
        kind = str(self.get(feature, "GetTypeName2"))
        require(kind == "Chamfer", f"native feature type was {kind}")
        definition = self.typed(self.get(feature, "GetDefinition"), "ChamferFeatureData2")
        require(bool(self.get(definition, "AccessSelections", self.model, Swapp.nothing())),
                "could not roll back the native chamfer selection")
        try:
            mode = self.get(definition, "Type")
            self.rec.data["last_chamfer_type"] = mode
            self.rec.flush()
            require(mode == self.constants["swChamferAngleDistance"], "native chamfer is outside the angle-distance profile")
            fields = {key: self.get(definition, key) for key in ("TangentPropagation", "KeepFeatures",
                      "PropagateFeatureToParts", "GetEdgeCount", "GetFaceCount", "LoopCount",
                      "EdgeChamferAngle")}
            fields["Type"] = mode
            fields["distance_by_side_m"] = [float(self.get(definition, "GetEdgeChamferDistance", side)) for side in (0, 1)]
            edges = tuple(self.get(definition, "Edges") or ())
            fields["alternate_inputs"] = {"faces": len(self.get(definition, "Faces") or ()),
                                          "loops": len(self.get(definition, "Loops") or ())}
            self.rec.data["last_native_definition"] = fields
            self.rec.flush()
            require(not any(fields[key] for key in ("TangentPropagation", "KeepFeatures", "PropagateFeatureToParts")),
                    "unexpected ordinary angle-distance modes")
            require(not any(fields["alternate_inputs"].values()) and fields["GetFaceCount"] in (-1, 0)
                    and fields["LoopCount"] in (-1, 0), "chamfer unexpectedly owns alternate inputs")
            require(fields["GetEdgeCount"] == len(edges) == 1 and edges[0] is not None,
                    "chamfer source selection is not one actual edge")
            edge, proof = self.find_edge(endpoints, boss)
            selected = self.typed(edges[0], "Edge")
            require(self.same(selected, edge), "rollback chamfer owns a different stock edge")
            fields["GetIsFlipped"] = self.get(definition, "GetIsFlipped", self.typed(selected, "Entity"))
            self.rec.flush()
            require(fields["GetIsFlipped"] is False, "actual selected chamfer edge differs from the requested flip state")
            self.rec.close_number("stored chamfer leading distance", fields["distance_by_side_m"][0], params[0])
            self.rec.close_number("stored chamfer angle", fields["EdgeChamferAngle"], params[1])
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        parents = tuple(self.get(feature, "GetParents") or ())
        require(any(self.same(parent, boss) for parent in parents), "chamfer lost its real blind boss parent")
        return {"type": kind, "fields": fields, "edge": proof, "feature_reference": self.reference(feature),
                "parents": [str(self.get(parent, "Name")) for parent in parents]}

    def driver_inventory(self, feature):
        preference = self.constants["swDisplayFeatureDimensions"]
        old = bool(self.get(self.model, "GetUserPreferenceToggle", preference))
        inventory, live = [], {}
        try:
            self.get(self.model, "SetUserPreferenceToggle", preference, True)
            require(bool(self.get(self.model, "GetUserPreferenceToggle", preference)), "cannot expose actual drivers")
            display = self.get(feature, "GetFirstDisplayDimension")
            while display is not None:
                require(len(inventory) < 16, "native chamfer dimension traversal exceeded its bound")
                kind = int(self.get(display, "Type2"))
                indexes = (0, 1) if kind == self.constants["swChamferDimension"] else (0,)
                for index in indexes:
                    self.read_driver(display, kind, index, inventory, live)
                display = self.get(feature, "GetNextDisplayDimension", display)
        finally:
            self.get(self.model, "SetUserPreferenceToggle", preference, old)
            require(bool(self.get(self.model, "GetUserPreferenceToggle", preference)) == old,
                    "unable to restore native display preference")
        self.rec.data["last_native_driver_inventory"] = inventory
        self.rec.flush()
        return inventory, live

    def display_drivers(self, feature, params):
        inventory, live = self.driver_inventory(feature)
        require(len(live) == 2, "expected two distinct actual driving chamfer handles")
        bindings = {}
        for role, expected in zip(ROLES, params, strict=True):
            matches = [(row, dimension) for row, dimension in live.values()
                       if math.isclose(row["value_si"], expected, rel_tol=0.0, abs_tol=1e-10)]
            require(len(matches) == 1, f"live chamfer handle for {role} is missing or ambiguous")
            bindings[role] = matches[0]
        require(len({row["name"] for row, _ in bindings.values()}) == 2, "chamfer drivers were aliased")
        return inventory, bindings

    def read_driver(self, display, kind, index, inventory, live):
        dimension = self.get(display, "GetDimension2", index)
        if dimension is None:
            inventory.append({"display_kind": kind, "index": index, "dimension": None})
            return
        dimension = self.typed(dimension, "Dimension")
        name = str(self.get(dimension, "FullName"))
        state, readonly = int(self.get(dimension, "DrivenState")), bool(self.get(dimension, "ReadOnly"))
        row = {"name": name, "value_si": float(self.get(dimension, "SystemValue")), "display_kind": kind,
               "index": index, "driven_state": state, "read_only": readonly}
        inventory.append(row)
        if state != self.constants["swDimensionDriving"] or readonly:
            return
        pieces = name.split("@")
        path = str(self.get(self.model, "GetPathName"))
        require(len(pieces) == 3 and re.fullmatch(r"D[1-9][0-9]*", pieces[0]) and pieces[1] == self.feature_name
                and (not path or pieces[2].casefold() == (Path(path).stem + ".Part").casefold()),
                f"unexpected editable model driver owner: {name}")
        require(name not in live or self.same(live[name][1], dimension), "two native handles use the same driver name")
        live[name] = row, dimension

    def edit(self, case):
        feature = self.get(self.model, "FeatureByName", CHAMFER)
        _, bindings = self.display_drivers(feature, values_si(case, False))
        role = next(iter(case["edit"]))
        row, dimension = bindings[role]
        target = values_si(case, True)[ROLES.index(role)]
        status = int(self.get(dimension, "SetSystemValue3", target, self.constants["swSetValue_InThisConfiguration"],
                              Swapp.nothing()))
        self.rec.data["edit"] = {"role": role, "driver": row, "target_si": target, "status": status}
        self.rec.flush()
        require(status == self.constants["swSetValue_Successful"], f"native chamfer driver edit returned {status}")
        self.rec.close_number("native right driver value after edit", self.get(dimension, "SystemValue"), target)

    def bevel_surface(self, body, feature):
        faces = [self.typed(face, "Face2") for face in self.get(body, "GetFaces") or ()]
        require(all(self.get(self.get(face, "GetSurface"), "IsPlane") for face in faces),
                "native chamfer boundary is not fully planar")
        owned = [face for face in faces if self.same(self.get(face, "GetFeature"), feature)]
        require(len(owned) == 1 and any(self.same(owned[0], member) for member in self.get(feature, "GetFaces") or ()),
                "expected exactly one actual bevel face produced by the chamfer")
        face = owned[0]
        edges = [self.typed(edge, "Edge") for edge in self.get(face, "GetEdges") or ()]
        require(len(edges) == 4, "bevel polygon is not a four-edge side of the prism")
        vertices = []
        for edge in edges:
            for point in self.edge_points(edge):
                if not any(equal_point(point, old) for old in vertices):
                    vertices.append(point)
        return {"vertices_m": vertices, "area_m2": float(self.get(face, "GetArea")), "reference": self.reference(face)}

    def close_six(self, label, actual, expected, near_zero):
        error, tolerance, passed = compare_six(actual, expected, near_zero)
        self.rec.data["checks"].append({"name": label, "actual": actual, "expected": expected,
                                         "absolute_error": error, "absolute_tolerance": tolerance,
                                         "method": "half_unit_at_sixth_significant_place_or_near_zero",
                                         "passed": passed})
        self.rec.flush()
        require(passed, f"{label}: native result differs at six significant figures")

    def check_face_areas(self, body, expected, label):
        areas = sorted(float(self.get(self.typed(face, "Face2"), "GetArea")) for face in self.get(body, "GetFaces") or ())
        for index, pair in enumerate(zip(areas, expected["face_areas"], strict=True)):
            self.close_six(f"{label} sorted face area {index}", *pair, near_zero=1e-16)
        return areas

    def snapshot(self, case, plan, label, *, edited=False):
        self.clean_rebuild()
        configurations = list(self.get(self.model, "GetConfigurationNames") or ())
        active = self.get(self.get(self.model, "ConfigurationManager"), "ActiveConfiguration")
        require(configurations == [str(self.get(active, "Name"))], "source is outside the sole ordinary configuration")
        tree = self.feature_tree(required_names=(SKETCH, BOSS, self.feature_name))
        names = [row["name"] for row in tree]
        require(names.index(BOSS) < names.index(self.feature_name), "native feature tree reordered the chamfer before its stock")
        stock = self.inspect_feature(BOSS, SKETCH, case["size_mm"][2], True)
        require(not stock["reverse"], "native box stock reversed its authored depth")
        profile, inverse = self.inspect_profile(SKETCH, self.profile(case))
        boss, feature = (self.get(self.model, "FeatureByName", name) for name in (BOSS, self.feature_name))
        params = self.profile_params(case, edited)
        endpoints = [self.transform(point, inverse) for point in plan["stock"]["source_edge"]]
        definition = self.definition(feature, boss, endpoints, params)
        body = self.one_body()
        bevel = self.bevel_surface(body, feature)
        self.rec.data["last_native_bevel_surface"] = bevel
        self.rec.flush()
        matches = []
        for option in plan["states"]["edited" if edited else "initial"]:
            branch, predicted = option["branch"], option["geometry"]
            expected = [self.transform(point, inverse) for point in predicted["bevel_vertices"]]
            try:
                same_points(bevel["vertices_m"], expected, "exact bevel polygon")
            except ValueError:
                continue
            matches.append((branch, predicted))
        require(len(matches) == 1, "actual bevel polygon does not identify one prospectively frozen analytic branch")
        branch, expected = matches[0]
        self.close_six(f"{label} bevel face area", bevel["area_m2"], expected["bevel_area"], near_zero=1e-16)
        areas = self.check_face_areas(body, expected, label)
        inventory, bindings = self.display_drivers(feature, params)
        result = {"tree": tree, "stock": stock, "profile": profile, "configurations": configurations,
                  "definition": definition, "body": self.measure_body(expected, inverse, label), "bevel": bevel,
                  "face_areas_m2": areas, "branch": list(branch), "legs_m": expected["legs_m"],
                  "driver_inventory": inventory, "drivers": {role: row for role, (row, _) in bindings.items()}}
        self.rec.data[label] = result
        self.rec.flush()
        return result
