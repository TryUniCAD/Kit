from __future__ import annotations

from argparse import ArgumentParser
import hashlib
import json
from math import dist, isclose, isfinite, radians
from pathlib import Path
import os
import re
from shutil import copytree
import time

from RevolveFamilyModel import (
    FEATURE_NAMES, PROFILE, STOCK_NAMES, WALL_TYPES, cut_predictions, edited_case,
    need, thin_predictions, validate_specs, world,
)


SCHEMA = "kit.sw2026.revolve-family-authoring.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
TOOLS = (
    "AuthorRevolveFamilies.py", "RevolveFamilyModel.py", "AuthorRevolveSources.py",
    "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
)
STOCK_SKETCHES = ("InnerStockSketch", "OuterStockSketch")
END_NAMES = (
    "SingleDir", "IsSolid", "IsThin", "IsCut", "ReverseDir", "BothDirectionUpToSameEntity",
    "Dir1Type", "Dir2Type", "Dir1Angle", "Dir2Angle", "OffsetReverse1", "OffsetReverse2",
    "OffsetDistance1", "OffsetDistance2", "ThinType", "ThinThickness1", "ThinThickness2",
    "Merge", "UseFeatScope", "UseAutoSelect",
)
LENGTH_TYPES = ("swLinearDimension", "swHorLinearDimension", "swVertLinearDimension")
ENUMS = {
    "swEndConditions_e": ("swEndCondBlind",),
    "swRevolveType_e": ("swRevolveTypeOneDirection",),
    "swThinWallType_e": tuple(WALL_TYPES.values()),
    "swSelectType_e": ("swSelSKETCHES", "swSelSKETCHSEGS", "swSelEXTSKETCHSEGS", "swSelSOLIDBODIES"),
    "swDimensionType_e": ("swAngularDimension", *LENGTH_TYPES),
    "swDimensionDrivenState_e": ("swDimensionDriving",),
    "swSetValueInConfiguration_e": ("swSetValue_InThisConfiguration",),
    "swBodyType_e": ("swSolidBody",),
    "swObjectEquality": ("swObjectSame",),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_hashes():
    return {name: digest(Path(__file__).with_name(name)) for name in TOOLS}


def constants_from_registration(sw):
    library = sw.pythoncom.LoadRegTypeLib("{4687F359-55D0-4CD3-B6CF-2EB42C11F989}", 34, 0, 0)
    attrs = library.GetLibAttr()
    need(attrs[3:5] == (34, 0), "wrong registered SwConst type library version")
    found = {}
    for index in range(library.GetTypeInfoCount()):
        name = library.GetDocumentation(index)[0]
        if name in ENUMS:
            info = library.GetTypeInfo(index)
            members = [info.GetVarDesc(member) for member in range(info.GetTypeAttr().cVars)]
            found[name] = {info.GetNames(member.memid)[0]: member.value for member in members}
    result = {}
    for name, members in ENUMS.items():
        need(name in found and all(type(found[name].get(member)) is int for member in members),
             f"registered 2026 vocabulary is incomplete for {name}")
        result.update({member: found[name][member] for member in members})
    return result


def feature_arguments(case, constants, *, cut=False, thin=False, merge=True, scoped=False):
    blind = constants["swEndCondBlind"]
    mode = WALL_TYPES[case["wall_mode"]] if thin else "swThinWallOneDirection"
    first, second = case["wall_m"] if thin else (0.0, 0.0)
    return (
        True, True, thin, cut, case["reverse"], False, blind, blind, radians(case["angle_deg"]), 0.0,
        False, False, 0.0, 0.0, constants[mode], first, second, merge, scoped, not scoped,
    )


def author_type(base, planes, sw, constants):
    class FamilyAuthor(base):
        def same(self, left, right):
            return int(self.get(self.app, "IsSame", left, right)) == constants["swObjectSame"]

        def check_axis(self, raw, case):
            observed = self.axis_data(raw)
            owner = self.get(self.typed(raw, "SketchSegment"), "GetSketch")
            need(owner is not None and self.same(owner, self.sketch), "actual selected line belongs to another sketch")
            for point, height in zip(observed["points"], case["axis_axial_m"], strict=True):
                for index, actual in enumerate(point):
                    expected = (case["axis_x_m"], height, 0.0)[index]
                    self.rec.close_number("axis endpoint " + "xyz"[index], actual, expected)
            need(len(observed["id"]) == 2, "unexpected construction line identity")
            return observed

        def sketch_features(self):
            result = {}
            feature = self.get(self.model, "FirstFeature")
            while feature is not None:
                if str(self.get(feature, "GetTypeName2")) == "ProfileFeature":
                    name = str(self.get(feature, "Name"))
                    need(name and name not in result, "profile feature names are not unique")
                    result[name] = feature
                feature = self.get(feature, "GetNextFeature")
            return result

        def make_profile(self, case, name, thin):
            prior = self.sketch_features()
            self.get(self.model, "ClearSelection2", True)
            extension = self.get(self.model, "Extension")
            need(self.get(extension, "SelectByID2", planes[case["plane"]], "PLANE",
                          0.0, 0.0, 0.0, False, 0, sw.nothing(), 0), "principal support selection failed")
            manager = self.get(self.model, "SketchManager")
            self.get(manager, "InsertSketch", True)
            self.sketch = self.get(manager, "ActiveSketch")
            need(self.sketch is not None, "active sketch unavailable")
            x = case["axis_x_m"]
            low, high = case["axial_m"]
            axis_low, axis_high = case["axis_axial_m"]
            self.set(manager, "AddToDB", True)
            try:
                if thin:
                    radius = x + case["profile_radius_m"]
                    line = self.get(manager, "CreateLine", radius, low, 0.0, radius, high, 0.0)
                    need(line is not None, "open wall-centre line creation failed")
                else:
                    inner, outer = case["radius_m"]
                    lines = self.get(manager, "CreateCornerRectangle", x + inner, low, 0.0, x + outer, high, 0.0)
                    need(lines is not None and len(lines) == 4, "closed rectangular profile creation failed")
                axis = self.get(manager, "CreateCenterLine", x, axis_low, 0.0, x, axis_high, 0.0)
                need(axis is not None, "construction line creation failed")
                original = self.axis_data(axis)
            finally:
                self.set(manager, "AddToDB", False)
            self.get(manager, "InsertSketch", True)
            current = self.sketch_features()
            created = current.keys() - prior.keys()
            need(len(created) == 1 and prior.keys() <= current.keys(),
                 "the new 2D profile must have one actual feature owner")
            sketch_feature = current[created.pop()]
            self.set(sketch_feature, "Name", name)
            self.sketch = self.get(sketch_feature, "GetSpecificFeature2")
            need(self.sketch is not None, "authored profile has no actual sketch interface")
            return original

        def mark_feature_inputs(self, case, profile, original, target):
            self.get(self.model, "ClearSelection2", True)
            selection = self.get(self.model, "SelectionManager")
            self.set(selection, "EnableContourSelection", False)
            extension = self.get(self.model, "Extension")
            need(self.get(extension, "SelectByID2", profile, "SKETCH", 0.0, 0.0, 0.0, False, 0, sw.nothing(), 0),
                 "mark zero sketch selection failed")
            height = sum(case["axis_axial_m"]) / 2
            point = self.world([case["axis_x_m"], height, 0.0])
            need(self.get(extension, "SelectByID2", f"{original['name']}@{profile}", "EXTSKETCHSEGMENT",
                          *point, True, 4, sw.nothing(), 0), "mark four construction line selection failed")
            if target is not None:
                select_data = self.get(selection, "CreateSelectData")
                self.set(select_data, "Mark", 1)
                need(self.get(target, "Select2", True, select_data), "mark one stock body selection failed")
            marks = {str(mark): int(self.get(selection, "GetSelectedObjectCount2", mark)) for mark in (-1, 0, 1, 4)}
            need(marks == {"-1": 2 + int(target is not None), "0": 1, "1": int(target is not None), "4": 1},
                 "actual marked selections differ from profile, axis and stock request")
            need(int(self.get(selection, "GetSelectedObjectType3", 1, 0)) == constants["swSelSKETCHES"],
                 "mark zero does not reference the sketch")
            axis_type = int(self.get(selection, "GetSelectedObjectType3", 1, 4))
            need(axis_type in (constants["swSelSKETCHSEGS"], constants["swSelEXTSKETCHSEGS"]),
                 "mark four does not identify a sketch segment")
            actual = self.check_axis(self.get(selection, "GetSelectedObject6", 1, 4), case)
            need(actual["id"] == original["id"], "selected a different construction line")
            body_name = None
            if target is not None:
                need(int(self.get(selection, "GetSelectedObjectType3", 1, 1)) == constants["swSelSOLIDBODIES"],
                     "mark one does not identify a solid body")
                selected = self.get(selection, "GetSelectedObject6", 1, 1)
                need(self.same(target, selected), "mark one selected a different body")
                body_name = self.body_owner(selected)[0]
            return {"marks": marks, "axis": actual, "body_producer": body_name}

        def add_revolve(self, case, profile, name, *, cut=False, thin=False, merge=True):
            original = self.make_profile(case, profile, thin)
            target = None
            if cut and case["scope"] != "all":
                selected_name = STOCK_NAMES[("inner", "outer").index(case["scope"])]
                target = self.stock_bodies()[selected_name][0]
            selected = self.mark_feature_inputs(case, profile, original, target)
            arguments = feature_arguments(case, constants, cut=cut, thin=thin, merge=merge, scoped=target is not None)
            self.rec.data.setdefault("feature_requests", []).append({
                "name": name, "selection": selected,
                "arguments": dict(zip(END_NAMES, arguments, strict=True)),
            })
            self.rec.flush()
            feature = self.get(self.get(self.model, "FeatureManager"), "FeatureRevolve2", *arguments)
            need(feature is not None, "FeatureRevolve2 returned no feature")
            self.set(feature, "Name", name)

        def build(self, case, session):
            self.model = self.rec.call("new independent part", session.new_part)
            cut = case["family"] == "cut"
            if cut:
                for index, name in enumerate(STOCK_NAMES):
                    stock = dict(case, angle_deg=360.0, reverse=False, axial_m=case["stock_axial_m"],
                                 radius_m=case["stock_radii_m"][index])
                    self.add_revolve(stock, STOCK_SKETCHES[index], name, merge=index == 0)
                need(bool(self.get(self.model, "ForceRebuild3", False)), "two-stock pre-cut rebuild failed")
                self.rec.data["pre_cut_bodies"] = self.observe_cut_bodies(case, before=True)
                self.rec.flush()
            self.add_revolve(case, PROFILE, FEATURE_NAMES[case["family"]], cut=cut, thin=not cut, merge=not cut)
            self.get(self.model, "ClearSelection2", True)

        def solids(self):
            part = self.typed(self.model, "PartDoc")
            return [self.typed(row, "Body2") for row in self.get(part, "GetBodies2", constants["swSolidBody"], False) or ()]

        def body_owner(self, body):
            body = self.typed(body, "Body2")
            owners = []
            faces = self.get(body, "GetFaces") or ()
            need(0 < len(faces) <= 50, "unexpected face inventory for an ordinary revolved body")
            for face in faces:
                feature = self.get(self.typed(face, "Face2"), "GetFeature")
                need(feature is not None, "actual body face lacks an owning feature")
                owners.append(str(self.get(feature, "Name")))
            stocks = set(owners).intersection(STOCK_NAMES)
            need(len(stocks) == 1 and set(owners) <= set(STOCK_NAMES) | {FEATURE_NAMES["cut"]},
                 "body does not resolve to one actual stock creator")
            return stocks.pop(), sorted(owners)

        def stock_bodies(self):
            bodies = self.solids()
            result = {}
            for body in bodies:
                owner, faces = self.body_owner(body)
                need(owner not in result, "two bodies claim the same stock creator")
                result[owner] = (body, faces)
            need(len(bodies) == 2 and result.keys() == set(STOCK_NAMES), "expected the two authored stock bodies")
            return result

        def body_state(self, body):
            raw = [float(value) for value in self.get(body, "GetMassProperties", 1.0)]
            need(len(raw) == 12 and all(isfinite(value) for value in raw)
                 and min(raw[3:6]) > 0 and isclose(raw[3], raw[5], rel_tol=2e-7), "per-body mass at density one is invalid")
            bounds = []
            for sign in (-1.0, 1.0):
                for axis in range(3):
                    direction = [0.0, 0.0, 0.0]
                    direction[axis] = sign
                    outputs = [sw.VARIANT(sw.pythoncom.VT_BYREF | sw.pythoncom.VT_R8, 0.0) for _ in range(3)]
                    reply = self.get(body, "GetExtremePoint", *direction, *outputs)
                    if isinstance(reply, tuple):
                        need(len(reply) == 4 and bool(reply[0]), "typed body extreme-point call failed")
                        bounds.append(float(reply[axis + 1]))
                    else:
                        need(bool(reply), "body extreme-point call failed")
                        bounds.append(float(outputs[axis].value))
            return {"name": str(self.get(body, "Name")), "com_m": raw[:3], "volume_m3": raw[3],
                    "area_m2": raw[4], "bounds_m": bounds,
                    "faces": int(self.get(body, "GetFaceCount")), "edges": int(self.get(body, "GetEdgeCount")),
                    "vertices": len(self.get(body, "GetVertices") or ())}

        def compare_body(self, label, actual, expected):
            self.rec.close_number(label + " volume m3", actual["volume_m3"], expected["volume_m3"], absolute=1e-22)
            self.rec.close_number(label + " area m2", actual["area_m2"], expected["area_m2"], absolute=1e-18)
            for field in ("com_m", "bounds_m"):
                for index, (value, reference) in enumerate(zip(actual[field], expected[field], strict=True)):
                    self.rec.close_number(f"{label} {field}[{index}]", value, reference, absolute=1e-10)
            need(actual["name"] and min(actual["faces"], actual["edges"]) > 0, "solid name or topology is empty")

        def observe_cut_bodies(self, case, *, before=False):
            bodies = self.stock_bodies()
            expected = cut_predictions(case, before=before)
            states = {}
            for owner, (body, faces) in bodies.items():
                row = self.body_state(body) | {"face_owners": faces, "cut_face": FEATURE_NAMES["cut"] in faces}
                states[owner] = row
            self.rec.data["last_cut_body_observation"] = states
            self.rec.flush()
            for owner, row in states.items():
                need(row["cut_face"] == expected[owner]["cut_face"], "cut face attached to a different stock")
                self.compare_body(owner, row, expected[owner])
            return {"measured": states, "expected": expected}

        def scope_state(self, case, definition):
            scoped = bool(self.get(definition, "FeatureScope"))
            automatic = bool(self.get(definition, "AutoSelect"))
            count = int(self.get(definition, "GetFeatureScopeBodiesCount"))
            bodies = self.get(definition, "FeatureScopeBodies")
            rows = [self.body_owner(body)[0] for body in bodies or ()]
            result = {"feature_scope": scoped, "auto_select": automatic, "count": count,
                      "array_present": bodies is not None, "stock_owners": rows}
            self.rec.data["last_scope_observation"] = result
            self.rec.flush()
            if case["scope"] == "all":
                need(not scoped and not rows, "unrestricted cut acquired a selected-body restriction")
            else:
                expected = STOCK_NAMES[("inner", "outer").index(case["scope"])]
                need(scoped and not automatic and count == 1 and rows == [expected],
                     "native cut definition does not retain its explicit stock owner")
                body = self.stock_bodies()[expected][0]
                need(self.same(body, bodies[0]), "definition stock owner differs from the rollback body object")
            return result

        def observe_profile(self):
            case = self.case
            frame_points = ([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])
            transform = [self.world(point) for point in frame_points]
            for actual, expected in zip(transform, [world(case, point) for point in frame_points], strict=True):
                need(all(isclose(a, b, abs_tol=1e-10) for a, b in zip(actual, expected, strict=True)),
                     "saved sketch transform differs from the intended canonical principal plane")
            segments = self.geometry()
            active = [row for row in segments if not row["construction"]]
            axes = [row for row in segments if row["construction"]]
            need(len(axes) == 1 and all(row["kind"] == "line" for row in segments), "profile needs one axis and only line edges")
            x = case["axis_x_m"]
            low, high = case["axial_m"]
            if case["family"] == "thin":
                radius = x + case["profile_radius_m"]
                need(len(active) == 1, "thin wall requires one open centreline segment")
                self.compare_point(active[0]["start"], (radius, low))
                self.compare_point(active[0]["end"], (radius, high))
            else:
                inner, outer = case["radius_m"]
                wanted = [(x + inner, low), (x + outer, low), (x + outer, high), (x + inner, high)]
                need(len(active) == 4, "rectangular cut profile needs four edges")
                for index, start in enumerate(wanted):
                    stop = wanted[(index + 1) % len(wanted)]
                    need(sum(self.same_side(row, start, stop) for row in active) == 1, "rectangle lost an actual profile edge")
            manager = self.get(self.model, "ConfigurationManager")
            config = self.get(manager, "ActiveConfiguration")
            return {"frame_points": transform, "segments": segments, "configuration": str(self.get(config, "Name"))}

        def compare_point(self, actual, expected):
            for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
                self.rec.close_number("profile coordinate " + str(index), left, right)

        def same_side(self, row, first, second):
            def near(left, right):
                return all(isclose(a, b, abs_tol=1e-10) for a, b in zip(left, right, strict=True))
            return (near(row["start"], first) and near(row["end"], second)) or (near(row["start"], second) and near(row["end"], first))

        def read_definition(self, case, feature):
            definition = self.typed(self.get(feature, "GetDefinition"), "RevolveFeatureData2")
            need(self.get(definition, "AccessSelections", self.model, sw.nothing()), "revolve definition selections unavailable")
            try:
                is_thin = bool(self.get(definition, "IsThinFeature"))
                is_boss = bool(self.get(definition, "IsBossFeature"))
                mode = int(self.get(definition, "Type"))
                direction = bool(self.get(definition, "ReverseDirection"))
                axis_type = int(self.get(definition, "GetAxisType"))
                angles = [float(self.get(definition, "GetRevolutionAngle", side)) for side in (True, False)]
                axis = self.check_axis(self.get(definition, "Axis"), case)
                row = {"is_thin": is_thin, "is_boss": is_boss, "type": mode, "reverse": direction,
                       "angles_rad": angles, "axis_type": axis_type, "axis": axis}
                self.rec.data["last_definition"] = row
                self.rec.flush()
                need(is_thin == is_boss == (case["family"] == "thin"), "native revolve operation differs from authored family")
                need(mode == constants["swRevolveTypeOneDirection"] and direction == case["reverse"],
                     "native angular end or reverse differs from authored intent")
                need(axis_type == constants["swSelSKETCHSEGS"], "revolve axis is not the selected sketch segment")
                self.rec.close_number("actual forward angle", angles[0], radians(case["angle_deg"]))
                self.rec.close_number("inactive reverse angle", angles[1], 0.0)
                if is_thin:
                    wall_mode = int(self.get(definition, "ThinWallType"))
                    widths = [float(self.get(definition, "GetWallThickness", side)) for side in (True, False)]
                    row.update(wall_mode=wall_mode, wall_getters_m=widths)
                    self.rec.flush()
                    need(wall_mode == constants[WALL_TYPES[case["wall_mode"]]], "native wall direction differs from the authored enum")
                    need(all(isfinite(value) and value >= 0 for value in widths) and any(widths), "native wall getters returned invalid values")
                else:
                    row["scope"] = self.scope_state(case, definition)
                return row
            finally:
                self.get(definition, "ReleaseSelectionAccess")

        def display_roles(self, case, feature):
            preference = self.display_dimension_preference()
            previous = bool(self.get(self.model, "GetUserPreferenceToggle", preference))
            try:
                self.get(self.model, "SetUserPreferenceToggle", preference, True)
                need(bool(self.get(self.model, "GetUserPreferenceToggle", preference)), "cannot enable live feature displays")
                return self.read_display_roles(case, feature)
            finally:
                self.get(self.model, "SetUserPreferenceToggle", preference, previous)
                need(bool(self.get(self.model, "GetUserPreferenceToggle", preference)) == previous, "display preference restoration failed")

        def read_display_roles(self, case, feature):
            rows = []
            display = self.get(feature, "GetFirstDisplayDimension")
            owner = FEATURE_NAMES[case["family"]]
            while display is not None:
                need(len(rows) < 16, "too many native display dimensions for the ordinary feature")
                param = self.get(display, "GetDimension2", 0)
                need(param is not None, "native display dimension has no dimension owner")
                name = str(self.get(param, "FullName"))
                kind = int(self.get(display, "Type2"))
                value = float(self.get(param, "SystemValue"))
                editable = not bool(self.get(param, "ReadOnly")) and int(self.get(param, "DrivenState")) == constants["swDimensionDriving"]
                rows.append(({"name": name, "kind": kind, "value": value, "editable": editable}, param))
                display = self.get(feature, "GetNextDisplayDimension", display)
            self.rec.data["last_display_dimensions"] = [row for row, _ in rows]
            self.rec.flush()
            driving = [(row, param) for row, param in rows if row["editable"]]
            need(all(row["name"].split("@")[1:2] == [owner] and isfinite(row["value"]) for row, _ in driving),
                 "active dimension belongs to a different named feature")
            requested = [("angle", radians(case["angle_deg"]), (constants["swAngularDimension"],), (1.0,))]
            if case["family"] == "thin":
                wall_types = tuple(constants[name] for name in LENGTH_TYPES)
                scales = (1.0, 0.5) if case["wall_mode"] == "midplane" else (1.0,)
                requested.append(("wall1", case["wall_m"][0], wall_types, scales))
                if case["wall_mode"] == "two":
                    requested.append(("wall2", case["wall_m"][1], wall_types, (1.0,)))
            roles = {}
            for key, value, kinds, scales in requested:
                candidates = [(row | {"display_scale": scale}, param) for row, param in driving
                              if row["kind"] in kinds for scale in scales
                              if isclose(row["value"], value * scale, rel_tol=2e-7, abs_tol=1e-12)]
                need(len(candidates) == 1, "no unique editable native driver for " + key)
                roles[key] = candidates[0]
            names = [row["name"] for row, _ in roles.values()]
            need(len(names) == len(set(names)) == len(driving), "native editable display inventory has extra or aliased owners")
            return roles

        def snapshot(self, case, label, angle_degrees):
            self.case = case
            need(angle_degrees == case["angle_deg"], "phase angle differs from its semantic case")
            need(bool(self.get(self.model, "ForceRebuild3", False)), "native revolve rebuild failed")
            need(int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0,
                 "document contains native errors or warnings")
            name = FEATURE_NAMES[case["family"]]
            required = (PROFILE, name, planes[case["plane"]])
            if case["family"] == "cut":
                required += STOCK_NAMES + STOCK_SKETCHES
            tree = self.feature_tree(required_names=required)
            feature, sketch = [self.get(self.model, "FeatureByName", key) for key in (name, PROFILE)]
            need(feature is not None and sketch is not None, "native feature or consumed sketch is absent")
            self.sketch = self.get(sketch, "GetSpecificFeature2")
            parents = [str(self.get(row, "Name")) for row in self.get(feature, "GetParents") or ()]
            need(PROFILE in parents and sum(row["name"] == name for row in tree) == 1,
                 "feature does not bind its unique named profile")
            profile = self.observe_profile()
            cut_geometry = self.observe_cut_bodies(case) if case["family"] == "cut" else {}
            definition = self.read_definition(case, feature)
            roles = self.display_roles(case, feature)
            observation = {"definition": definition, "feature_type": str(self.get(feature, "GetTypeName2")),
                           "features": tree, "parents": parents, "profile": profile,
                           "drivers": {key: row for key, (row, _) in roles.items()},
                           "body_count": len(self.solids())}
            self.rec.data[label] = observation
            self.rec.flush()
            if case["family"] == "thin":
                bodies = self.solids()
                need(len(bodies) == 1, "thin revolve must produce one real solid")
                actual = self.body_state(bodies[0])
                expected = thin_predictions(case)
                sign, prediction = min(expected, key=lambda item: dist(actual["com_m"], item[1]["com_m"]))
                observation.update(measured=actual, expected=prediction, first_wall_sign=sign)
                self.rec.flush()
                self.compare_body(label, actual, prediction)
            else:
                observation.update(cut_geometry)
            self.rec.flush()
            return feature

        def edit_angle(self, case, feature):
            current = dict(case)
            final = edited_case(case)
            pending = tuple(self.display_roles(case, feature))
            edits = []
            for index, key in enumerate(pending):
                row, param = self.read_display_roles(current, feature)[key]
                if key == "angle":
                    current["angle_deg"] = final["angle_deg"]
                    target = radians(final["angle_deg"])
                else:
                    slot = int(key[-1]) - 1
                    current["wall_m"] = list(current["wall_m"])
                    current["wall_m"][slot] = final["wall_m"][slot]
                    target = final["wall_m"][slot] * row["display_scale"]
                status = int(self.get(param, "SetSystemValue3", target, constants["swSetValue_InThisConfiguration"], sw.nothing()))
                need(status == 0, "live drive setter failed for " + key)
                self.rec.close_number("edited display " + key, self.get(param, "SystemValue"), target)
                label = "edited" if index == len(pending) - 1 else "after-" + key
                feature = self.snapshot(current, label, current["angle_deg"])
                need(self.rec.data[label]["drivers"][key]["name"] == row["name"], "edit changed the dimension owner's identity")
                edits.append({"role": key, "dimension": row["name"], "before": row["value"], "after": target, "status": status})
            self.rec.data["edit"] = {"passed": True, "dimensions": edits}
            self.rec.flush()

    return FamilyAuthor


def check_hash(value):
    need(type(value) is str and re.fullmatch(r"[a-f0-9]{64}", value), "expected a SHA-256 identity")
    return value


def check_git_identity(value):
    need(type(value) is str and re.fullmatch(r"[a-f0-9]{40}", value), "expected a full Git SHA-1 object identity")
    return value


def prepare(args):
    from pathlib import PureWindowsPath

    spec = json.loads(args.spec.read_bytes())
    validate_specs(spec)
    paths = {"spec": args.guest_spec, "control": args.control, "output": args.output,
             "publication": args.publication, "checkout": args.checkout}
    need(all(PureWindowsPath(value).is_absolute() for value in paths.values()), "guest paths must be absolute")
    return {
        "schema": SCHEMA,
        "source_revision": check_git_identity(args.source_revision),
        "source_tree": check_git_identity(args.source_tree),
        "spec_sha256": digest(args.spec),
        "control_sha256": check_hash(args.control_sha256),
        "oracle_sha256": ORACLE,
        "tool_sha256": tool_hashes(),
        **paths,
    }


def native_source(case, output, run_phase, author):
    directory = output / case["name"]
    directory.mkdir()
    source = directory / f"{case['name']}.SLDPRT"
    derivative = directory / f"{case['name']}-edited.SLDPRT"
    written = run_phase(case, "author", source, ORACLE, author_type=author)
    phase_results = [written]
    native_hash = written[0].get("native_sha256")
    if written[0]["passed"]:
        reopened = run_phase(case, "reopen", source, ORACLE, native_hash,
                             inspect_before_rebuild=True, save_edited=derivative, author_type=author)
        phase_results.append(reopened)
        if reopened[0]["passed"] and reopened[0].get("edit", {}).get("passed"):
            phase_results.append(run_phase(edited_case(case), "edited-reopen", derivative, ORACLE,
                                           reopened[0]["edited_derivative"]["sha256"],
                                           inspect_before_rebuild=True, author_type=author))
    passed = len(phase_results) == 3 and all(phase["passed"] for phase, _ in phase_results)
    if passed:
        saved, edited, reopened_after = [row for row, _ in phase_results]
        states = (saved["authored"], edited["reopened"], edited["edited"], reopened_after["reopened"])
        names = [{key: row["name"].split("@")[:2] for key, row in state["drivers"].items()} for state in states]
        body_count = 1 if case["family"] == "thin" else 2
        passed = (digest(source) == native_hash and all(row == names[0] for row in names)
                  and all(row["features"] == states[0]["features"] for row in states)
                  and all(row["before_explicit_rebuild"]["bodies"] == body_count
                          and row["before_explicit_rebuild"]["whats_wrong"] == 0
                          for row in (edited, reopened_after)))
    return {"native_sha256": native_hash, "native_bytes": written[0].get("native_bytes"),
            "phases": [
                {"phase": row["job"]["phase"], "sha256": receipt, "passed": row["passed"],
                 "open_status": row.get("open_status"),
                 "checks": len(row["checks"]), "checks_passed": sum(check["passed"] for check in row["checks"])}
                for row, receipt in phase_results
            ], "passed": passed}, [row for row, _ in phase_results]


def execute(job_path):
    need(os.name == "nt", "native source acquisition runs on the designated Windows guest")
    import Swapp
    from AuthorCurves import write_json
    from AuthorRevolveSources import PLANES, RevolveAuthor, run_phase
    from InspectFresh import healthy, inspect

    job_path = job_path.resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    need(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE, "wrong authoring protocol or executable pin")
    for name in ("source_revision", "source_tree"):
        check_git_identity(job[name])
    checkout = Path(job["checkout"]).resolve(strict=True)
    spec_path, control, output, publication = (Path(job[name]).resolve() for name in ("spec", "control", "output", "publication"))
    tools = tool_hashes()
    need(tools == job["tool_sha256"], "staged tool closure differs from the frozen job")
    need(all(not path.is_relative_to(checkout) for path in (Path(__file__).resolve(), job_path, spec_path, control, output, publication)),
         "research job, tools and artifacts belong outside the SDK checkout")
    need(not output.exists() and not publication.exists() and not publication.is_relative_to(output)
         and not output.is_relative_to(publication), "raw and publication paths must be fresh independent destinations")
    need(digest(spec_path) == check_hash(job["spec_sha256"]) and digest(control) == check_hash(job["control_sha256"]),
         "source specification or control digest mismatch")
    spec = json.loads(spec_path.read_bytes())
    cases = validate_specs(spec)
    if spec["split"] == "heldout":
        need(all(path.drive.casefold() == "c:" for path in (job_path, spec_path, output)),
             "held-out job, specification and native artifacts must reside on the guest local C drive")
    need(not Swapp.application_pids() and not Swapp.owned_process_ids(), "native application is already active")
    job_digest = digest(job_path)
    constants = constants_from_registration(Swapp)
    author = author_type(RevolveAuthor, PLANES, Swapp, constants)
    output.mkdir(parents=True)
    evidence = {
        "schema": "kit.sw2026.revolve-family-source-lock.v1", "family": spec["family"], "split": spec["split"],
        "source_revision": job["source_revision"], "source_tree": job["source_tree"], "job_sha256": job_digest,
        "spec_sha256": job["spec_sha256"], "control_sha256": job["control_sha256"], "tool_sha256": tools,
        "oracle_sha256": ORACLE, "oracle_build": "34.5.2.0604", "registered_swconst": constants,
        "started_at": time.time(), "sources": [], "writer_output_count": 0, "heldout_writer_acceptance": False,
    }
    processes = []
    signs = set()

    def record_process(result):
        if "oracle_identity" in result:
            processes.append(result["oracle_identity"]["process_creation_filetime"])

    def control_phase(label):
        result = inspect(control)
        path = output / f"{label}.json"
        write_json(path, result)
        record_process(result)
        evidence[label] = {
            "sha256": digest(path),
            "passed": bool(healthy(result) and result["sha256"] == job["control_sha256"]
                           and result["oracle_identity"]["sha256"] == ORACLE),
        }

    try:
        control_phase("control-before")
        if evidence["control-before"]["passed"]:
            for index, case in enumerate(cases, 1):
                row, phases = native_source(case, output, run_phase, author)
                identity = case["name"] if spec["split"] == "discovery" else f"Slot{index:02}"
                evidence["sources"].append({"case": identity, **row})
                for phase in phases:
                    record_process(phase)
                    if spec["family"] == "thin":
                        signs.update(value["first_wall_sign"] for key, value in phase.items()
                                     if key in ("authored", "reopened", "edited") or key.startswith("after-")
                                     if isinstance(value, dict) and value.get("first_wall_sign") is not None)
    except Exception as error:
        write_json(output / "PrivateFailure.json", {"error": repr(error)})
        evidence["batch_exception"] = True
    finally:
        try:
            control_phase("control-after")
        except Exception as error:
            write_json(output / "PrivateControlFailure.json", {"error": repr(error)})
            evidence["control-after"] = {"passed": False}

    evidence.update(
        finished_at=time.time(), fresh_processes=len(processes), distinct_processes=len(set(processes)),
        idle_after=not Swapp.application_pids() and not Swapp.owned_process_ids(),
        inputs_unchanged=(digest(spec_path) == job["spec_sha256"] and digest(control) == job["control_sha256"]
                          and digest(job_path) == job_digest),
        tools_unchanged=tool_hashes() == tools,
        wall_side_consistent=len(signs) <= 1,
    )
    if spec["family"] == "thin" and spec["split"] == "discovery":
        evidence["measured_first_wall_signs"] = sorted(signs)
    evidence["passed"] = bool(
        evidence.get("control-before", {}).get("passed") and evidence["control-after"]["passed"]
        and evidence["fresh_processes"] == evidence["distinct_processes"] == 2 + 3 * len(cases)
        and evidence["idle_after"] and evidence["inputs_unchanged"] and evidence["tools_unchanged"]
        and evidence["wall_side_consistent"] and not evidence.get("batch_exception")
        and len(evidence["sources"]) == len(cases) and all(row["passed"] for row in evidence["sources"])
    )
    write_json(output / "SourceLock.json", evidence)
    if spec["split"] == "heldout":
        publication.parent.mkdir(parents=True, exist_ok=True)
        write_json(publication, evidence)
    else:
        copytree(output, publication)
    Swapp.emit({"passed": evidence["passed"], "sources": len(evidence["sources"]),
                "source_lock_sha256": digest(output / "SourceLock.json"), "writer_output_count": 0})
    return int(not evidence["passed"])


def preflight(spec_path):
    spec = json.loads(spec_path.read_bytes())
    cases = validate_specs(spec)
    need(spec["split"] == "discovery", "only disclosed model intentions may be printed by preflight")
    answers = {}
    for case in cases:
        if case["family"] == "thin":
            answers[case["name"]] = {"before": thin_predictions(case), "after": thin_predictions(edited_case(case))}
        else:
            answers[case["name"]] = {"stock": cut_predictions(case, before=True), "before": cut_predictions(case),
                                     "after": cut_predictions(edited_case(case))}
    return {"spec_sha256": digest(spec_path), "family": spec["family"], "expected_native_launches": 2 + 3 * len(cases),
            "analytic_predictions": answers}


def static_manifest(binary):
    from runpy import run_path
    from struct import unpack

    binary = binary.resolve(strict=True)
    need(not any((parent / ".git").exists() for parent in binary.parents),
         "licensed module must be outside repository checkouts")
    image_hash = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
    need(digest(binary) == image_hash, "expected exact SP05.2 model module")
    helper = Path(__file__).with_name("body") / "PinNativeNames.py"
    helper_hash = "ffa6f015b152d2aa0ce869afc94665e5f01f5089d23298fa19681ff2ac7dc7b9"
    need(digest(helper) == helper_hash, "PE source-range helper changed")
    image = run_path(str(helper))["Image"](binary)
    need(image.base == 0x4B140000 and len(image.data) == 46536280, "model image layout changed")
    shapes = {
        "moRevolution_c": (0x4D185908, 0x4BB1E7A0),
        "moRevolutionThin_c": (0x4D187FC0, 0x4BB1E5F0),
        "moRevCut_c": (0x4CF52450, 0x4BB1E7A0),
        "moThinSpec_c": (0x4D202298, 0x4BB22C80),
    }
    tables = {}
    for label, (address, serializer) in shapes.items():
        actual = unpack("<Q", image.at(address + 0x28, 8))[0]
        need(actual == serializer, "runtime serializer virtual changed for " + label)
        tables[label] = {"vtable": hex(address), "serializer": hex(actual)}
    ranges = {
        "ordinary_cut_constructor": (0x4C389EE0, 0x4C389F3C),
        "thin_revolve_constructor": (0x4C38A7B0, 0x4C38A94F),
        "thin_spec_constructor": (0x4C6EEEB0, 0x4C6EEF45),
        "thin_spec_get_thickness": (0x4C6EF010, 0x4C6EF020),
        "thin_spec_get_thickness2": (0x4C6EF000, 0x4C6EF010),
        "thin_spec_set_thickness2": (0x4C6EF240, 0x4C6EF257),
        "thin_primary_constructor_display": (0x4C38A858, 0x4C38A883),
        "thin_secondary_constructor_display": (0x4C38A8A3, 0x4C38A8CE),
        "thin_spec_assign_feature_fields": (0x4C38A917, 0x4C38A928),
        "thin_spec_read_direction": (0x4B2845F0, 0x4B2845F4),
        "thin_spec_read_cap_ends": (0x4B289A60, 0x4B289A64),
        "thin_spec_read_end_thickness": (0x4B347920, 0x4B347926),
        "thin_spec_read_add_bends": (0x4B283940, 0x4B283944),
        "atom_selected_feature_scope": (0x4B2867D0, 0x4B2867D7),
        "atom_all_body_feature_scope": (0x4B28D860, 0x4B28D86C),
        "atom_set_feature_scope": (0x4B2924F0, 0x4B2924F7),
    }
    rows = {}
    for label, (lower, upper) in ranges.items():
        rows[label] = {"start": hex(lower), "end_exclusive": hex(upper),
                       "file_offset": image.offset(lower - image.base, upper - lower),
                       "sha256": hashlib.sha256(image.at(lower, upper - lower)).hexdigest()}
    return {"schema": "kit.sw2026.revolve-family-static.v1", "oracle_build": "34.5.2.0604",
            "module": binary.name, "module_sha256": image_hash, "image_base": hex(image.base),
            "source_range_helper_sha256": helper_hash, "runtime_classes": tables,
            "source_ranges": rows, "native_execution": False}


def main():
    parser = ArgumentParser(description="Acquire and lock ordinary native thin revolve or revolve cut sources")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("spec", type=Path)
    for key in ("guest-spec", "control", "output", "publication", "checkout",
                "source-revision", "source-tree", "control-sha256"):
        plan.add_argument("--" + key, required=True)
    check = sub.add_parser("preflight")
    check.add_argument("spec", type=Path)
    pin = sub.add_parser("static")
    pin.add_argument("model_dll", type=Path)
    run = sub.add_parser("run")
    run.add_argument("job", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        return execute(args.job)
    if args.command == "static":
        answer = static_manifest(args.model_dll)
    else:
        answer = prepare(args) if args.command == "plan" else preflight(args.spec)
    print(json.dumps(answer, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
