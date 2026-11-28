from math import atan2, dist, isclose, pi

from AuthorReferencePlaneSources import CONSTANTS, LIBRARY, PlaneAuthor, metadata as plane_metadata
from ReferencePlaneDimensions import member
from C057PlacementPlan import NAMES, ROLES, add, cross, dot, require, unit

FRONT = "Front Plane"
CALLS = {
    "IFeatureManager": {"FeatureExtrusion3": 23},
    "ISketchManager": {"CreateLine": 6, "InsertSketch": 1, "ActiveSketch": 0},
    "ISketch": {"ModelToSketchTransform": 0, "GetSketchSegments": 0},
    "ISketchLine": {"GetStartPoint2": 0, "GetEndPoint2": 0},
    "ISketchSegment": {"Select4": 2, "GetID": 0},
    "ISketchRelationManager": {"AddRelation": 2},
    "IModelDoc2": {"AddDimension2": 3, "ForceRebuild3": 1},
    "IDimension": {"SetSystemValue3": 3},
    "IBody2": {"GetVertices": 0, "GetEdges": 0, "GetFaces": 0},
}
ENUMS = {
    "swConstraintType_e": {"swConstraintType_COINCIDENT": 9, "swConstraintType_FIXED": 17,
                           "swConstraintType_PARALLEL": 7, "swConstraintType_PERPENDICULAR": 8},
    "swRefPlaneReferenceConstraints_e": {"swRefPlaneReferenceConstraint_Coincident": 4},
    "swDimensionType_e": {"swAngularDimension": 3, "swLinearDimension": 2},
}


def metadata():
    base = plane_metadata()
    import Swapp

    com = Swapp.pythoncom
    com.CoInitialize()
    try:
        libraries = [com.LoadRegTypeLib(identity, 34, 0, 0) for identity in (LIBRARY, CONSTANTS)]
        methods, enums = {}, {}
        for library in libraries:
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                attrs = info.GetTypeAttr()
                if name in CALLS:
                    for slot in range(attrs.cFuncs):
                        binding = info.GetFuncDesc(slot)
                        names = list(info.GetNames(binding.memid))
                        if not names or names[0] not in CALLS[name] or binding.invkind not in (1, 2):
                            continue
                        key = f"{name}.{names[0]}"
                        require(key not in methods and len(binding.args) == CALLS[name][names[0]],
                                "unexpected native binding or argument count: " + key)
                        methods[key] = {"id": binding.memid, "invoke_kind": binding.invkind,
                                        "names": names, "args": repr(binding.args), "return": repr(binding.rettype)}
                if name in (*ENUMS, "swUserPreferenceToggle_e"):
                    keys = set(ENUMS.get(name, {"swInputDimValOnCreate": None}))
                    for slot in range(attrs.cVars):
                        binding = info.GetVarDesc(slot)
                        key = info.GetNames(binding.memid)[0]
                        if key in keys:
                            require(type(binding.value) is int, "registered COM constant is not an integer")
                            enums[key] = binding.value
        require(set(methods) == {f"{owner}.{name}" for owner, members in CALLS.items() for name in members},
                "missing declared C057 API methods")
        require(all(enums.get(name) == value for values in ENUMS.values() for name, value in values.items())
                and "swInputDimValOnCreate" in enums, "required C057 API constants differ")
        return base | {"placement_methods": methods, "placement_enums": enums}
    finally:
        com.CoUninitialize()


def close_points(actual, expected, title):
    require(len(actual) == len(expected), title + " count differs")
    identities = [tuple(i for i, reference in enumerate(expected) if dist(value, reference) <= 2e-8)
                  for value in actual]
    require(all(len(row) == 1 for row in identities) and len(set(identities)) == len(expected),
            title + " does not match the independent world points")


class PlacedStockAuthor(PlaneAuthor):
    def feature(self, role):
        name = NAMES.get(role, role)
        value = self.get(self.model, "FeatureByName", name)
        require(value is not None and self.get(value, "Name") == name, "missing actual feature " + name)
        return value

    def frame_for(self, transform):
        utility = self.get(self.app, "GetMathUtility")
        result = []
        for vector in ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
            wrapped = self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, vector)
            point = self.get(utility, "CreatePoint", wrapped)
            result.append(tuple(float(x) for x in self.get(self.get(point, "MultiplyTransform", transform), "ArrayData")))
        origin, *basis = result
        u, v, n = (add(value, origin, -1.0) for value in basis)
        require(all(isclose(dot(x, x), 1.0, abs_tol=2e-12) for x in (u, v, n))
                and dist(cross(u, v), n) <= 2e-10, "native measured frame is nonrigid")
        return origin, u, v, n

    def sketch_frame(self):
        return self.frame_for(self.get(self.get(self.sketch, "ModelToSketchTransform"), "Inverse"))

    def frame_point(self, frame, world):
        origin, u, v, n = frame
        offset = add(world, origin, -1.0)
        require(abs(dot(offset, n)) < 2e-8, "authored point is outside its actual supporting sketch")
        return dot(offset, u), dot(offset, v), 0.0

    def world_on(self, frame, local):
        origin, *axes = frame
        for axis, distance in zip(axes, local, strict=True):
            origin = add(origin, axis, distance)
        return origin

    def relation_on(self, kind, entities):
        array = self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_DISPATCH, list(entities))
        ids = sorted(tuple(self.get(entity, "GetID")) for entity in entities)
        relation = self.get(self.get(self.sketch, "RelationManager"), "AddRelation", array, kind)
        require(relation is not None and self.get(relation, "GetRelationType") == kind
                and not self.get(relation, "Suppressed"), "native sketch relation was rejected or suppressed")
        result = self.get(relation, "GetEntities")
        require(sorted(tuple(self.get(entity, "GetID")) for entity in result) == ids,
                "native relation did not retain its exact selected owners")

    def ends(self, segment):
        line = self.typed(segment, "SketchLine")
        return self.get(line, "GetStartPoint2"), self.get(line, "GetEndPoint2")

    def line(self, manager, frame, points, construction=False):
        coords = tuple(value for point in points for value in self.frame_point(frame, point))
        segment = self.get(manager, "CreateLine", *coords)
        require(segment is not None, "native line creation failed")
        self.set(segment, "ConstructionGeometry", construction)
        observed = tuple(self.world_on(frame, self.point(point)) for point in self.ends(segment))
        require(all(dist(value, expected) <= 2e-8 for value, expected in zip(observed, points, strict=True)),
                "native line did not retain the directed model-space endpoints")
        return segment

    def enter(self, support):
        before = {name for _, name, _ in self.top_features()}
        self.get(self.model, "ClearSelection2", True)
        require(self.get(support, "Select2", False, 0), "could not select the actual sketch support")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        self.sketch = self.get(manager, "ActiveSketch")
        require(self.sketch is not None, "the selected plane did not acquire a sketch")
        return manager, before

    def leave(self, manager, before, role):
        self.get(manager, "InsertSketch", True)
        found, = (feature for feature, name, kind in self.top_features()
                  if kind == "ProfileFeature" and name not in before)
        self.set(found, "Name", NAMES[role])
        return found

    def same_owner(self, actual, choices):
        if actual is None:
            return False
        if not hasattr(actual, "_oleobj_"):
            actual = self.sw.wc.Dispatch(actual)
        app = self.app
        for expected in choices:
            if int(self.get(app, "IsSame", actual, expected)) == 1:
                return True
            iid = self.sw.pythoncom.IID_IUnknown
            if actual._oleobj_.QueryInterface(iid) == expected._oleobj_.QueryInterface(iid):
                return True
        return False

    def read_angle(self, plane, hinge, front):
        front_native = self.get(front, "GetSpecificFeature2")
        plane_native = self.declared_interface(self.get(plane, "GetSpecificFeature2"), "IRefPlane")
        plane_frame = self.frame_for(self.get(plane_native, "Transform"))
        definition = self.declared_interface(self.get(plane, "GetDefinition"), "IRefPlaneFeatureData")
        require(self.get(definition, "AccessSelections", self.model, self.sw.nothing()),
                "actual selected Front and hinge references cannot be accessed")
        try:
            constraints = [int(self.indexed(definition, "Constraint", row)) for row in (0, 1)]
            reference_plane = self.indexed(definition, "Reference", 0)
            reference_line = self.indexed(definition, "Reference", 1)
            value = float(self.indexed(definition, "AngleOrDistance", 0))
            binds = [self.same_owner(reference_plane, (front, front_native)), self.same_owner(reference_line, (hinge,))]
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        evidence = {"constraints": constraints, "reference_slots_owned": binds, "angle_magnitude": value,
                    "plane_frame": plane_frame}
        self.rec.data["selected_datum_before_sketch"] = evidence
        self.rec.flush()
        return evidence

    def observe_datum(self, expected, evidence):
        world = expected["frame"]
        origin, _, _, normal = world
        plane_frame = evidence["plane_frame"]
        sketch_frame = self.sketch_frame()
        roll = atan2(dot(world[1], sketch_frame[2]), dot(world[1], sketch_frame[1]))
        evidence = {**evidence, "sketch_frame": sketch_frame, "source_frame": world,
                    "in_plane_roll_rad": roll,
                    "normal_offset_m": dot(add(plane_frame[0], origin, -1), normal)}
        self.rec.data["datum_checkpoint"] = evidence
        self.rec.flush()
        require([row & 0xFF for row in evidence["constraints"]] == [16, 4] and all(evidence["reference_slots_owned"]),
                "angular plane lost its real selected plane/line or the declared slot order")
        self.rec.close_number("native selected angle magnitude", evidence["angle_magnitude"], abs(expected["drivers"]["Angle"]))
        require(dist(plane_frame[3], normal) <= 2e-8 and dist(sketch_frame[3], normal) <= 2e-8
                and abs(evidence["normal_offset_m"]) <= 2e-8
                and abs(dot(add(sketch_frame[0], origin, -1), normal)) <= 2e-8,
                "actual signed datum or attached sketch plane does not contain the source placement")
        return evidence

    def add_edge_dimension(self, segment, witness, value, role):
        self.get(self.model, "ClearSelection2", True)
        require(self.get(segment, "Select4", False, self.sw.nothing()), "real stock edge could not be selected")
        display = self.get(self.model, "AddDimension2", *witness)
        require(display is not None and member(self, display, "IDisplayDimension", "Type2") == 2,
                "selected edge did not create an ordinary true-length dimension")
        dimension = member(self, display, "IDisplayDimension", "GetDimension2", 0)
        require(dimension is not None, "native true-length dimension has no actual parameter")
        self.rec.close_number("actual unedited " + role, member(self, dimension, "IDimension", "SystemValue"), value)
        self.dimension_objects[role] = dimension

    def profile(self, plane, datum, expected):
        manager, before = self.enter(plane)
        observed = self.observe_datum(expected, datum)
        frame = observed["sketch_frame"]
        corners = expected["outline"]
        origin, u, v, _ = expected["frame"]
        length, width = (expected["drivers"][key] for key in ("Length", "Width"))
        guide_start = add(origin, v, -0.2 * width)
        self.set(manager, "AddToDB", True)
        try:
            sides = tuple(self.line(manager, frame, (a, b))
                          for a, b in zip(corners, (*corners[1:], corners[0]), strict=True))
            guide = self.line(manager, frame, (guide_start, add(guide_start, u, length * 0.3)), True)
        finally:
            self.set(manager, "AddToDB", False)
        ends = tuple(self.ends(row) for row in sides)
        for index, (_, finish) in enumerate(ends):
            start = ends[(index + 1) % 4][0]
            if tuple(self.get(start, "GetID")) != tuple(self.get(finish, "GetID")):
                self.relation_on(9, (finish, start))
        for point in (*self.ends(guide), ends[0][0]):
            self.relation_on(17, (point,))
        self.relation_on(7, (sides[0], sides[2]))
        self.relation_on(7, (sides[1], sides[3]))
        self.relation_on(8, (sides[0], sides[1]))
        self.relation_on(7, (sides[0], guide))
        enum = self.api["placement_enums"]["swInputDimValOnCreate"]
        original = self.get(self.app, "GetUserPreferenceToggle", enum)
        try:
            self.get(self.app, "SetUserPreferenceToggle", enum, False)
            require(self.get(self.app, "GetUserPreferenceToggle", enum) is False,
                    "could not disable the native modified-dimension prompt")
            self.add_edge_dimension(sides[0], add(add(origin, u, 0.5 * length), v, -0.12 * width), length, "Length")
            self.add_edge_dimension(sides[3], add(add(origin, v, 0.5 * width), u, -0.12 * length), width, "Width")
        finally:
            self.get(self.app, "SetUserPreferenceToggle", enum, original)
            require(self.get(self.app, "GetUserPreferenceToggle", enum) == original, "native preference was not restored")
        return self.leave(manager, before, "sketch")

    def build(self, case, oracle):
        expected = self.frozen_predictions["Original"]
        self.model = self.rec.call("new native C057 stock part", oracle.new_part)
        front = self.feature(FRONT)
        manager, before = self.enter(front)
        frame = self.sketch_frame()
        origin = case["origin_m"]
        extent = min(case["original"]["Length"], case["original"]["Width"]) / 2
        points = (add(origin, case["axis"], -extent), add(origin, case["axis"], extent))
        self.set(manager, "AddToDB", True)
        try:
            hinge = self.line(manager, frame, points, True)
        finally:
            self.set(manager, "AddToDB", False)
        endpoints = self.ends(hinge)
        for point in endpoints:
            self.relation_on(17, (point,))
        start, finish = (self.world_on(frame, self.point(value)) for value in endpoints)
        actual = unit(add(finish, start, -1.0))
        self.leave(manager, before, "hinge")
        self.get(self.model, "ClearSelection2", True)
        require(self.get(front, "Select2", False, 0), "actual Front reference selection failed")
        selection = self.get(self.model, "SelectionManager")
        marks = self.get(selection, "CreateSelectData")
        self.set(marks, "Mark", 1)
        require(self.get(hinge, "Select4", True, marks), "actual construction hinge selection failed")
        front_native = self.declared_interface(self.get(front, "GetSpecificFeature2"), "IRefPlane")
        require(self.get(selection, "GetSelectedObjectCount2", -1) == 2
                and [self.get(selection, "GetSelectedObjectMark", index) for index in (1, 2)] == [0, 1]
                and self.same_owner(self.get(selection, "GetSelectedObject6", 1, -1), (front, front_native))
                and self.same_owner(self.get(selection, "GetSelectedObject6", 2, -1), (hinge,)),
                "native selection marks or actual Front/line targets differ")
        front_normal = self.frame_for(self.get(front_native, "Transform"))[3]
        normal = expected["frame"][3]
        angle = atan2(dot(actual, cross(front_normal, normal)), dot(front_normal, normal))
        require(0.0 < abs(angle) < pi / 2 and isclose(abs(angle), abs(case["original"]["Angle"]), abs_tol=2e-10),
                "actual selected hinge and Front normal imply an unmodeled angle branch")
        before = {name for _, name, _ in self.top_features()}
        manager = self.get(self.model, "FeatureManager")
        created = self.get(manager, "InsertRefPlane", 16 | (256 if angle < 0 else 0), abs(angle), 4, 0.0, 0, 0.0)
        require(created is not None, "native Front/line angular plane creation failed")
        plane, = (feature for feature, name, kind in self.top_features() if kind == "RefPlane" and name not in before)
        self.set(plane, "Name", NAMES["plane"])
        datum = self.read_angle(plane, hinge, front)
        sketch = self.profile(plane, datum, expected)
        self.get(self.model, "ClearSelection2", True)
        require(self.get(sketch, "Select2", False, 0), "actual rectangle profile selection failed")
        arguments = (True, False, False, 0, 0, expected["drivers"]["Height"], 0.0,
                     False, False, False, False, 0.0, 0.0, False, False, False, False,
                     True, True, True, 0, 0.0, False)
        boss = self.get(manager, "FeatureExtrusion3", *arguments)
        require(boss is not None, "ordinary blind stock boss creation failed")
        self.set(boss, "Name", NAMES["boss"])
        self.driver_names = {
            role: "@".join(member(self, self.dimension_objects[role], "IDimension", "FullName").split("@")[:2])
            for role in ROLES[:2]
        } | {"Height": "D1@" + NAMES["boss"], "Angle": "D1@" + NAMES["plane"]}

    def driver(self, role, observed_name):
        owner = NAMES[{"Length": "sketch", "Width": "sketch", "Height": "boss", "Angle": "plane"}[role]]
        parameter = self.get(self.model, "Parameter", observed_name)
        require(parameter is not None and observed_name.split("@")[1:] == [owner]
                and member(self, parameter, "IDimension", "FullName").split("@")[:2] == observed_name.split("@")
                and member(self, parameter, "IDimension", "DrivenState") == 2
                and not member(self, parameter, "IDimension", "ReadOnly"),
                role + " is missing its editable native feature owner")
        feature = self.feature(owner)
        display = member(self, feature, "IFeature", "GetFirstDisplayDimension")
        count, matches = 0, []
        while display is not None:
            count += 1
            require(count <= 8, "native display traversal exceeded the bounded stock profile")
            child = member(self, display, "IDisplayDimension", "GetDimension2", 0)
            if member(self, child, "IDimension", "FullName").split("@")[:2] == observed_name.split("@"):
                matches.append(member(self, display, "IDisplayDimension", "Type2"))
                require(self.same_owner(parameter, (child,)), "display and parameter ownership contradict one another")
            display = member(self, feature, "IFeature", "GetNextDisplayDimension", display)
        require(matches == [3 if role == "Angle" else 2], "native driver has the wrong or ambiguous display kind")
        return parameter

    def edit(self, role, value):
        parameter = self.driver(role, self.driver_names[role])
        require(self.get(parameter, "SetSystemValue3", abs(value), 1, self.sw.nothing()) == 0,
                "independent native " + role + " edit failed")

    def snapshot(self, case, state):
        from AuthorAssemblySources import feature_tree

        expected = self.frozen_predictions[state]
        require(self.get(self.model, "ForceRebuild3", False), "native stock rebuild failed")
        extension = self.get(self.model, "Extension")
        require(self.get(extension, "GetWhatsWrongCount") == self.get(extension, "NeedsRebuild2") == 0,
                "native stock has feature errors or pending rebuild")
        plane, sketch, boss = (self.feature(role) for role in ("plane", "sketch", "boss"))
        hinge_sketch = self.get(self.feature("hinge"), "GetSpecificFeature2")
        (hinge,) = self.get(hinge_sketch, "GetSketchSegments")
        self.sketch = hinge_sketch
        hinge_frame = self.sketch_frame()
        start, end = (self.world_on(hinge_frame, self.point(point)) for point in self.ends(hinge))
        half_span = min(case["original"][key] for key in ROLES[:2]) / 2
        require(self.get(hinge, "ConstructionGeometry")
                and dist(start, add(case["origin_m"], case["axis"], -half_span)) <= 2e-8
                and dist(end, add(case["origin_m"], case["axis"], half_span)) <= 2e-8,
                "actual hinge changed its anchored finite endpoints or direction")
        datum = self.read_angle(plane, hinge, self.feature(FRONT))
        self.sketch = self.get(sketch, "GetSpecificFeature2")
        datum = self.observe_datum(expected, datum)
        parents = {role: [str(self.get(parent, "Name")) for parent in self.get(feature, "GetParents") or ()]
                   for role, feature in (("plane", plane), ("sketch", sketch), ("boss", boss))}
        require(NAMES["plane"] in parents["sketch"] and NAMES["sketch"] in parents["boss"],
                "actual downstream sketch/boss dependency changed")
        tree = feature_tree(self, self.model)
        require(all(row["error"] == 0 and not row["warning"] and not row["suppressed"] for row in tree),
                "native stock tree contains rebuild errors, warnings or suppression")
        dimensions = {}
        for role, value in expected["drivers"].items():
            parameter = self.driver(role, self.driver_names[role])
            dimensions[role] = float(member(self, parameter, "IDimension", "SystemValue"))
            self.rec.close_number(role + " value in independent state", dimensions[role], abs(value))
        require(len(set(self.driver_names.values())) == 4, "distinct stock intents share one native driver")
        outline = self.get(self.sketch, "GetSketchSegments")
        sides = [row for row in outline if not self.get(row, "ConstructionGeometry")]
        require(len(sides) == 4 and len(outline) == 5, "native profile lost rectangle or isolated roll guide")
        frame = datum["sketch_frame"]
        corners = expected["outline"]
        pairs = set()
        for segment in sides:
            actual = (self.world_on(frame, self.point(value)) for value in self.ends(segment))
            matches = [tuple(i for i, corner in enumerate(corners) if dist(point, corner) <= 2e-8)
                       for point in actual]
            require(all(len(found) == 1 for found in matches), "native profile corner is missing or ambiguous")
            pairs.add(frozenset(found[0] for found in matches))
        require(pairs == {frozenset((index, (index + 1) % 4)) for index in range(4)},
                "native rectangle changed its four actual consecutive edges")
        part = self.typed(self.model, "PartDoc")
        (body,) = self.get(part, "GetBodies2", 0, False)
        vertices = [tuple(self.get(value, "GetPoint")) for value in self.get(body, "GetVertices")]
        close_points(vertices, expected["vertices"], "native physical vertex")
        require(len(self.get(body, "GetFaces")) == 6 and len(self.get(body, "GetEdges")) == 12,
                "native solid did not retain its complete box incidence")
        mass = self.rec.call("measure actual solid", self.sw.mass, self.model)
        require(mass and "error" not in mass, "native body mass properties are unavailable")
        for key in ("volume", "area"):
            self.rec.close_number(key, mass[key], expected[key], absolute=1e-12)
        require(dist(mass["com"], expected["centroid"]) <= 2e-8, "independent world centroid differs")
        bounds = tuple(op(value[axis] for value in vertices) for op in (min, max) for axis in range(3))
        require(all(abs(actual - target) <= 2e-8 for actual, target in zip(bounds, expected["bounds"], strict=True)),
                "native physical bounds differ")
        return {"state": state, "tree": tree, "parents": parents, "datum": datum, "drivers": dimensions,
                "vertices": vertices, "bounds": bounds, "mass": mass, "body_count": 1}
