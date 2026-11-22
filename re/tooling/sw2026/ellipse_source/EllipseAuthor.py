import math
from pathlib import Path

import Swapp
from AuthorCurves import digest
from ChamferModel import compare_six
from FilletApi import CONSTS_LIB, MODEL_LIB, load
from FilletAuthor import FilletAuthor
from SelectedBodyMass import selected_body_mass

from EllipseModel import require


FRONT, SKETCH, BOSS = "Front Plane", "EllipseProfile", "EllipseBoss"
METHODS = {
    "ISketchManager": {"CreateEllipse": 9, "InsertSketch": 1},
    "ISketch": {"GetSketchSegments": 0, "GetSketchContours": 0, "GetReferenceEntity": 1,
                "ModelToSketchTransform": 0},
    "ISketchSegment": {"GetType": 0, "GetID": 0, "ConstructionGeometry": 0},
    "ISketchEllipse": {"GetCenterPoint2": 0, "GetMajorPoint2": 0, "GetMinorPoint2": 0},
    "ISketchContour": {"IsClosed": 0, "GetSketchSegments": 0},
    "IFeatureManager": {"FeatureExtrusion3": 23},
    "IFeature": {"Parameter": 1, "GetFaces": 0, "GetParents": 0},
    "ISelectionMgr": {"GetSelectedObjectCount2": 1, "GetSelectedObject6": 2},
    "IBody2": {"GetFaces": 0, "GetExtremePoint": 6, "Select2": 2},
    "IFace2": {"GetFeature": 0, "GetBody": 0, "GetSurface": 0, "GetEdges": 0, "GetArea": 0, "Normal": 0,
               "GetLoopCount": 0},
    "IEdge": {"GetCurve": 0, "GetTwoAdjacentFaces2": 0, "GetCurveParams3": 0},
    "ICurve": {"IsEllipse": 0, "GetEllipseParams": 0, "GetEndParams": 4},
    "ICurveParamData": {"StartPoint": 0, "EndPoint": 0, "UMinValue": 0, "UMaxValue": 0, "Sense": 0},
    "IModelDocExtension": {"CreateMassProperty2": 0},
    "IMassProperty2": {"AccuracyLevel": 0, "UseSystemUnits": 0, "SelectedItems": 0, "Recalculate": 0,
                       "GetOverrideOptions": 0, "Volume": 0, "SurfaceArea": 0, "CenterOfMass": 0, "Mass": 0},
    "IMassPropertyOverrideOptions": {"OverrideMass": 0, "OverrideCenterOfMass": 0},
    "IDimension": {"FullName": 0, "SystemValue": 0, "DrivenState": 0, "ReadOnly": 0, "SetSystemValue3": 3},
}
ENUMS = {
    "swSketchSegments_e": {"swSketchELLIPSE": 2},
    "swSelectType_e": {"swSelDATUMPLANES": 4},
    "swBodyType_e": {"swSolidBody": 0, "swSheetBody": 1},
    "swEndConditions_e": {"swEndCondBlind": 0},
    "swDimensionDrivenState_e": {"swDimensionDriving": 2},
    "swSetValueInConfiguration_e": {"swSetValue_InThisConfiguration": 1},
    "swSetValueReturnStatus_e": {"swSetValue_Successful": 0},
    "swObjectEquality": {"swObjectSame": None},
    "swMassPropertyAccuracyLevel_e": {"swMassPropertyAccuracyLevel_Higher": 2},
}
MASS_SETTERS = {"AccuracyLevel": 3, "UseSystemUnits": 11}


def installed_api():
    model, model_id = load(Swapp, MODEL_LIB)
    consts, const_id = load(Swapp, CONSTS_LIB)
    found, enums, setters = {}, {}, {}
    for index in range(model.GetTypeInfoCount()):
        name = model.GetDocumentation(index)[0]
        if name not in METHODS:
            continue
        info = model.GetTypeInfo(index)
        observed = {}
        for offset in range(info.GetTypeAttr().cFuncs):
            member = info.GetFuncDesc(offset)
            names = info.GetNames(member.memid)
            if (name == "IMassProperty2" and names and names[0] in MASS_SETTERS
                    and member.invkind == Swapp.pythoncom.INVOKE_PROPERTYPUT):
                require(tuple(arg[0] for arg in member.args) == (MASS_SETTERS[names[0]],),
                        f"registered IMassProperty2.{names[0]} setter type differs")
                setters[names[0]] = {"id": member.memid, "arguments": repr(member.args)}
            if not names or names[0] not in METHODS[name] or member.invkind not in (
                Swapp.pythoncom.INVOKE_FUNC, Swapp.pythoncom.INVOKE_PROPERTYGET,
            ):
                continue
            require(len(member.args) == METHODS[name][names[0]], f"registered {name}.{names[0]} arity differs")
            if names[0] == "CreateEllipse":
                require(tuple(args[0] for args in member.args) == (5,) * 9,
                        "native CreateEllipse does not accept nine double coordinates")
            observed[names[0]] = {"names": list(names), "id": member.memid, "invoke": member.invkind,
                                  "arguments": repr(member.args), "return": repr(member.rettype)}
        require(observed.keys() == METHODS[name].keys(), f"unregistered {name} members: {METHODS[name].keys() - observed.keys()}")
        found[name] = observed
    for index in range(consts.GetTypeInfoCount()):
        name = consts.GetDocumentation(index)[0]
        if name not in ENUMS:
            continue
        info = consts.GetTypeInfo(index)
        values = {info.GetNames(var.memid)[0]: var.value
                  for var in (info.GetVarDesc(i) for i in range(info.GetTypeAttr().cVars))}
        for member, expected in ENUMS[name].items():
            value = values.get(member)
            require(type(value) is int and (expected is None or value == expected), f"unverified enumeration: {member}")
            enums[member] = value
    require(found.keys() == METHODS.keys() and len(enums) == sum(map(len, ENUMS.values()))
            and setters.keys() == MASS_SETTERS.keys(), "incomplete 2026 ellipse API")
    return {"model": model_id, "constants": const_id, "members": found, "enums": enums, "mass_property_setters": setters}


class EllipseAuthor(FilletAuthor):
    def vector(self, label, actual, expected, absolute=1e-10):
        for i, pair in enumerate(zip(actual, expected, strict=True)):
            self.rec.close_number(f"{label} {i}", *pair, absolute=absolute)

    def identity(self, entity):
        values = list(self.get(entity, "GetID"))
        require(len(values) == 2 and all(type(value) is int for value in values), "native sketch ID is not an integer pair")
        return values

    def segment(self, sketch, plan, drawn=None):
        (segment,) = self.get(sketch, "GetSketchSegments") or ()
        require(int(self.get(segment, "GetType")) == self.constants["swSketchELLIPSE"]
                and not bool(self.get(segment, "ConstructionGeometry")), "profile left the actual nonconstruction ellipse path")
        segment_id = self.identity(segment)
        if drawn is not None:
            require(self.identity(drawn) == segment_id, "returned ellipse is not the active sketch member")
        ellipse = self.typed(segment, "SketchEllipse")
        points, ids = {}, {}
        for name, expected in zip(("Center", "Major", "Minor"), plan["points_m"], strict=True):
            point = self.typed(self.get(ellipse, f"Get{name}Point2"), "SketchPoint")
            points[name] = self.point(point)
            ids[name] = self.identity(point)
            self.vector(f"signed ellipse {name}", points[name], expected)
        require(len({tuple(value) for value in ids.values()}) == 3, "ellipse point roles alias in the native sketch")
        return {"segment_id": segment_id, "point_ids": ids, "points_m": points}

    def selected(self, expected):
        selection = self.get(self.model, "SelectionManager")
        require(all(int(self.get(selection, "GetSelectedObjectCount2", mark)) == 1 for mark in (-1, 0))
                and self.same(self.get(selection, "GetSelectedObject6", 1, 0), expected),
                "actual marked feature is not the intended owner")

    def profile(self, sketch, plan):
        observed = self.segment(sketch, plan)
        (contour,) = self.get(sketch, "GetSketchContours") or ()
        (member,) = self.get(contour, "GetSketchSegments") or ()
        require(bool(self.get(contour, "IsClosed")) and self.identity(member) == observed["segment_id"],
                "actual closed sketch contour does not own the full ellipse")
        plane = self.get(self.model, "FeatureByName", FRONT)
        datum = self.get(plane, "GetSpecificFeature2")
        ref_type = Swapp.byref_long()
        owner = self.get(sketch, "GetReferenceEntity", ref_type)
        require(int(ref_type.value) == self.constants["swSelDATUMPLANES"]
                and (self.same(owner, datum) or self.same(owner, plane)), "profile lost its actual origin Front Plane support")
        direct = self.get(sketch, "ModelToSketchTransform")
        matrix = list(self.get(direct, "ArrayData"))[:13]
        self.vector("canonical Front sketch frame", matrix, [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], 1e-12)
        relation_manager = self.get(sketch, "RelationManager")
        relations = [int(self.get(relation, "GetRelationType"))
                     for relation in self.get(relation_manager, "GetRelations", 0) or ()]
        observed.update(contour_closed=True, contour_members=1, support=FRONT, support_kind=int(ref_type.value),
                        frame=matrix, relation_types=relations)
        self.rec.data["last_profile"] = observed
        self.rec.flush()
        require(not relations, "unrepresented native sketch relation in free ellipse profile")
        return observed

    def author(self, session, plan):
        template = Path(self.rec.call("default native part template", session.template, "part"))
        require(template.is_absolute() and template.is_file(), "missing actual blank-part template")
        self.rec.data["template_sha256"] = digest(template)
        self.model = self.rec.call("new blank native part", session.new_part)
        require(digest(template) == self.rec.data["template_sha256"], "native part template changed")
        plane = self.get(self.model, "FeatureByName", FRONT)
        require(self.get(plane, "GetTypeName2") == "RefPlane", "canonical Front feature is not an actual datum")
        require(self.get(plane, "Select2", False, 0), "canonical Front feature cannot be selected")
        self.selected(plane)
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        sketch = self.get(manager, "ActiveSketch")
        require(sketch is not None, "ellipse must be drawn in a selected active 2D profile")
        before = bool(self.get(manager, "AddToDB"))
        self.set(manager, "AddToDB", True)
        try:
            coords = [value for point in plan["points_m"] for value in point]
            drawn = self.get(manager, "CreateEllipse", *coords)
            require(drawn is not None, "native CreateEllipse returned no sketch entity")
            self.rec.data["first_draw"] = self.segment(sketch, plan, drawn)
            self.rec.flush()
        finally:
            self.set(manager, "AddToDB", before)
        self.get(manager, "InsertSketch", True)
        feature = self.created_sketch_feature()
        self.set(feature, "Name", SKETCH)
        self.rec.data["before_boss"] = self.profile(self.get(feature, "GetSpecificFeature2"), plan)
        self.rec.flush()
        self.get(self.model, "ClearSelection2", True)
        require(self.get(feature, "Select2", False, 0), "ellipse profile cannot be selected for the boss")
        self.selected(feature)
        blind = self.constants["swEndCondBlind"]
        depth = plan["states"][0]["depth_m"]
        args = (True, False, False, blind, blind, depth, 0.0, False, False, False, False, 0.0, 0.0,
                False, False, False, False, True, True, True, 0, 0.0, False)
        boss = self.get(self.get(self.model, "FeatureManager"), "FeatureExtrusion3", *args)
        require(boss is not None, "native FeatureExtrusion3 did not make the ellipse boss")
        self.set(boss, "Name", BOSS)
        self.get(self.model, "ClearSelection2", True)

    def driver(self, feature, depth):
        alias = str(self.get(self.typed(self.get(feature, "Parameter", "D1"), "Dimension"), "FullName"))
        dimension = self.typed(self.get(self.model, "Parameter", f"D1@{BOSS}"), "Dimension")
        name = str(self.get(dimension, "FullName"))
        value = float(self.get(dimension, "SystemValue"))
        state, readonly = int(self.get(dimension, "DrivenState")), bool(self.get(dimension, "ReadOnly"))
        require(name == alias and name.split("@")[:2] == ["D1", BOSS] and not readonly
                and state == self.constants["swDimensionDriving"], "native D1 is not this boss's live driver")
        self.rec.close_number("native D1 value", value, depth)
        return dimension, {"name": name, "state": state, "readonly": readonly, "value_m": value}

    def edit(self, plan):
        boss = self.get(self.model, "FeatureByName", BOSS)
        dimension, initial = self.driver(boss, plan["states"][0]["depth_m"])
        depth = plan["states"][1]["depth_m"]
        status = int(self.get(dimension, "SetSystemValue3", depth, self.constants["swSetValue_InThisConfiguration"], Swapp.nothing()))
        self.rec.data["driver_edit"] = {"before": initial, "requested_m": depth, "setter_status": status}
        self.rec.flush()
        require(status == self.constants["swSetValue_Successful"], "actual D1 depth setter failed")

    def full_trim(self, edge, curve):
        trim = self.typed(self.get(edge, "GetCurveParams3"), "CurveParamData")
        low, high = (float(self.get(trim, name)) for name in ("UMinValue", "UMaxValue"))
        seam = [[float(value) for value in self.get(trim, name)] for name in ("StartPoint", "EndPoint")]
        ends = [Swapp.VARIANT(Swapp.pythoncom.VT_BYREF | Swapp.pythoncom.VT_R8, 0.0) for _ in range(2)]
        closed, periodic = Swapp.byref_bool(), Swapp.byref_bool()
        success = bool(self.get(curve, "GetEndParams", *ends, closed, periodic))
        period = abs(float(ends[1].value) - float(ends[0].value))
        observation = {"trim": [low, high], "base": [float(item.value) for item in ends], "period": period,
                       "seam_points_m": seam, "same_sense": bool(self.get(trim, "Sense")), "success": success,
                       "closed": bool(closed.value), "periodic": bool(periodic.value)}
        self.rec.data["last_rim_trim"] = observation
        self.rec.flush()
        require(success and observation["closed"] and observation["periodic"] and period > 0
                and all(math.isfinite(value) for value in (low, high, period)) and low != high
                and all(len(point) == 3 for point in seam), "native cap does not carry a finite whole periodic trim")
        self.rec.close_number("physical cap covers one period", abs(high - low), period, absolute=1e-11)
        self.vector("physical cap closed seam", *seam)
        return observation

    def cap(self, face, side, plan, expected):
        normal = [float(v) for v in self.get(face, "Normal")]
        require(len(normal) == 3 and abs(normal[2]) > 0.99, "cap is not normal to the signed sketch frame")
        i = int(normal[2] > 0)
        self.vector("native outward cap normal", normal, [0, 0, -1 if i == 0 else 1])
        require(int(self.get(face, "GetLoopCount")) == 1, "ellipse cap does not have exactly one boundary loop")
        (edge,) = self.get(face, "GetEdges") or ()
        curve = self.typed(self.get(edge, "GetCurve"), "Curve")
        require(bool(self.get(curve, "IsEllipse")), "actual cap rim is not a native ellipse")
        owners = self.get(edge, "GetTwoAdjacentFaces2") or ()
        require(len(owners) == 2 and all(any(self.same(owner, expected_face) for owner in owners)
                                         for expected_face in (face, side)), "cap rim does not join the actual cap and lateral faces")
        params = [float(v) for v in self.get(curve, "GetEllipseParams")]
        require(len(params) == 11 and all(math.isfinite(value) for value in params), "native kernel ellipse has invalid parameters")
        self.vector("physical cap ellipse centre", params[:3], [*plan["points_m"][0][:2], expected["depth_m"] * i])
        self.vector("physical cap ellipse semiaxes", [params[3], params[7]], plan["radii_m"])
        for native, model in zip((params[4:7], params[8:11]), plan["unit_axes"], strict=True):
            sign = math.fsum(a * b for a, b in zip(native, model, strict=True))
            self.vector("physical cap ellipse carrier axis", native, model if sign > 0 else [-value for value in model])
        approximate = float(self.get(face, "GetArea"))
        require(math.isfinite(approximate) and approximate > 0, "native cap area approximation is not finite and positive")
        trim = self.full_trim(edge, curve)
        area = math.pi * params[3] * params[7]
        self.rec.close_number("complete physical cap rim area", area, expected["cap_m2"], absolute=1e-16)
        return {"station": i, "params": params, "normal": normal, "edge_reference": self.reference(edge),
                "trim": trim, "area_from_rim_m2": area, "approximate_native_area_m2": approximate}

    def body_metric(self, label, actual, expected, near_zero):
        error, tolerance, passed = compare_six(actual, expected, near_zero)
        self.rec.data["checks"].append({"name": label, "actual": actual, "expected": expected,
                                        "passed": passed, "absolute_error": error,
                                        "absolute_tolerance": tolerance,
                                        "method": "half_unit_at_sixth_significant_place_or_near_zero"})
        self.rec.flush()
        require(passed, f"{label} differs from the independent analytic prediction")

    def measure(self, boss, plan, expected):
        body = self.one_body()
        faces = [self.typed(value, "Face2") for value in self.get(body, "GetFaces") or ()]
        produced = self.get(boss, "GetFaces") or ()
        require(len(faces) == len(produced) == 3
                and all(self.same(self.get(face, "GetBody"), body) and self.same(self.get(face, "GetFeature"), boss)
                        and any(self.same(face, member) for member in produced) for face in faces),
                "actual single solid faces do not all belong to this boss")
        planar = [bool(self.get(self.get(face, "GetSurface"), "IsPlane")) for face in faces]
        require(sum(planar) == 2, "elliptic extrusion must have two planar cap faces")
        mass = selected_body_mass(self, body)
        self.body_metric("ellipse boss volume", mass["volume"], expected["volume_m3"], 1e-21)
        self.body_metric("ellipse boss total area", mass["area"], expected["area_m2"], 1e-16)
        for axis, (actual, predicted) in enumerate(zip(mass["com"], expected["com_m"], strict=True)):
            self.body_metric(f"ellipse boss centre of mass {axis}", actual, predicted, 1e-12)
        side = faces[planar.index(False)]
        caps = [self.cap(face, side, plan, expected) for face, is_plane in zip(faces, planar, strict=True) if is_plane]
        require({cap["station"] for cap in caps} == {0, 1}, "both caps are on the same signed station")
        approximate = float(self.get(side, "GetArea"))
        require(math.isfinite(approximate) and approximate > 0, "native lateral face area approximation is not finite and positive")
        lateral = mass["area"] - math.fsum(cap["area_from_rim_m2"] for cap in caps)
        self.body_metric("lateral area from measured body and physical caps", lateral, expected["side_m2"], 1e-16)
        bounds = []
        for axis, interval in enumerate(expected["bounds_m"]):
            actual = []
            for sign in (-1, 1):
                unit = [float(sign) if index == axis else 0.0 for index in range(3)]
                values = [Swapp.VARIANT(Swapp.pythoncom.VT_BYREF | Swapp.pythoncom.VT_R8, 0.0) for _ in range(3)]
                require(bool(self.get(body, "GetExtremePoint", *unit, *values)), "actual ellipse bound query failed")
                actual.append(float(values[axis].value))
            self.vector(f"actual ellipse bound {axis}", actual, interval)
            bounds.append(actual)
        return {"mass": mass, "caps": caps, "solid_count": 1, "faces": 3, "bounds_m": bounds,
                "lateral_area_m2": lateral, "approximate_lateral_area_m2": approximate}

    def snapshot(self, label, plan, edited=False):
        self.clean_rebuild()
        configs = list(self.get(self.model, "GetConfigurationNames") or ())
        active = self.get(self.get(self.model, "ConfigurationManager"), "ActiveConfiguration")
        require(configs == [str(self.get(active, "Name"))], "source must have one ordinary active configuration")
        sketch = self.get(self.model, "FeatureByName", SKETCH)
        boss = self.get(self.model, "FeatureByName", BOSS)
        expected = plan["states"][int(edited)]
        tree = self.feature_tree(required_names=(SKETCH, BOSS))
        definition = self.inspect_feature(BOSS, SKETCH, expected["depth_m"] * 1000, True)
        require(not definition["reverse"], "boss reversed its single forward direction")
        profile = self.profile(self.get(sketch, "GetSpecificFeature2"), plan)
        driver = self.driver(boss, expected["depth_m"])[1]
        self.rec.data.update(last_definition=definition, last_driver=driver)
        self.rec.flush()
        require(self.get(sketch, "GetTypeName2") == "ProfileFeature" and SKETCH in definition["children"],
                "boss does not own its actual ellipse profile feature")
        self.rec.data[label] = {"configurations": configs, "tree": tree, "definition": definition,
                                "profile": profile, "driver": driver, "body": self.measure(boss, plan, expected)}
        self.rec.flush()
