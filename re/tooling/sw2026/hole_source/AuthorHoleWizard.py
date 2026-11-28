from math import dist, isclose

from AuthorCurves import CurveAuthor
from HoleWizardPlan import HOLE, STOCK, PARAMETERS, require
from ReadHoleApi import source_enums

FRONT = "Front Plane"


class HoleAuthor(CurveAuthor):
    def __init__(self, application, recorder, modules):
        super().__init__(application, recorder, modules)
        bindings = self.rec.call("bind installed object equality", source_enums)
        self.constants = {"swObjectSame": bindings["same_object"]}

    def feature(self, name, kind):
        result = self.get(self.model, "FeatureByName", name)
        require(result is not None and self.get(result, "Name") == name
                and self.get(result, "GetTypeName2") == kind, "missing actual native " + name)
        return result

    def body(self):
        part = self.typed(self.model, "PartDoc")
        bodies = self.get(part, "GetBodies2", 0, False)
        require(bodies is not None and len(bodies) == 1, "source must retain one actual solid")
        return bodies[0]

    def stock(self, case, controller):
        width, height, depth = case["stock_m"]
        self.model = self.rec.call("new native slab document", controller.new_part)
        front = self.feature(FRONT, "RefPlane")
        require(self.get(front, "Select2", False, 0), "stock sketch principal face selection failed")
        sketch_manager = self.get(self.model, "SketchManager")
        self.get(sketch_manager, "InsertSketch", True)
        self.set(sketch_manager, "AddToDB", True)
        try:
            rows = self.get(sketch_manager, "CreateCornerRectangle", 0.0, 0.0, 0.0, width, height, 0.0)
            require(rows and len(rows) == 4, "ordinary four-segment stock sketch failed")
        finally:
            self.set(sketch_manager, "AddToDB", False)
        self.get(sketch_manager, "InsertSketch", True)
        self.get(self.model, "ClearSelection2", True)
        sketch = self.created_sketch_feature()
        self.set(sketch, "Name", "Stock Profile")
        require(self.get(sketch, "Select2", False, 0), "ordinary stock profile selection failed")
        manager = self.get(self.model, "FeatureManager")
        args = (True, False, False, 0, 0, depth, 0.0, False, False, False, False,
                0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        extrusion = self.get(manager, "FeatureExtrusion3", *args)
        require(extrusion is not None, "could not author the plain stock feature")
        self.set(extrusion, "Name", STOCK)
        require(self.get(self.model, "ForceRebuild3", False), "native stock does not rebuild")
        body = self.body()
        require(len(self.get(body, "GetFaces")) == 6, "stock must be a rectangular slab")
        observed = self.rec.call("measure uncut stock", self.sw.mass, self.model)
        require(observed and "error" not in observed, "native slab mass was not measured")
        self.rec.close_number("uncut stock volume in SI", observed["volume"], width * height * depth)

    def owning_face(self, point):
        extension = self.get(self.model, "Extension")
        self.get(self.model, "ClearSelection2", True)
        require(self.get(extension, "SelectByID2", "", "FACE", *point, False, 0, self.sw.nothing(), 0),
                "face selection at the independently authored point did not resolve")
        manager = self.get(self.model, "SelectionManager")
        require(self.get(manager, "GetSelectedObjectCount2", -1) == 1
                and self.get(manager, "GetSelectedObjectMark", 1) == 0,
                "native Hole Wizard selection set or mark differs")
        face = self.typed(self.get(manager, "GetSelectedObject6", 1, -1), "Face2")
        body = self.get(face, "GetBody")
        observed = self.get(manager, "GetSelectionPoint2", 1, -1)
        self.rec.data["stock_selection"] = {"world_pick_m": observed, "normal": self.get(face, "Normal"), "mark": 0}
        self.rec.flush()
        require(observed and dist(observed, point) <= 2e-8
                and self.same(body, self.body())
                and self.get(self.get(face, "GetSurface"), "IsPlane")
                and dist(self.get(face, "Normal"), (0.0, 0.0, 1.0)) <= 2e-9,
                "face selection lost the target slab top, owner or exact pick point")

    def author(self, job, controller):
        case = job["case"]
        self.stock(case, controller)
        self.owning_face(job["original"]["point_m"])
        manager = self.typed(self.get(self.model, "FeatureManager"), "FeatureManager")
        hole = self.get(manager, "HoleWizard5", *(job["call"][name] for name in PARAMETERS))
        require(hole is not None and self.get(hole, "GetTypeName2") == "HoleWzd",
                "installed HoleWizard5 did not return a real Hole Wizard feature")
        self.set(hole, "Name", HOLE)
        self.get(self.model, "ClearSelection2", True)

    def definition(self, feature):
        data = self.typed(self.get(feature, "GetDefinition"), "WizardHoleFeatureData2")
        require(self.get(data, "AccessSelections", self.model, self.sw.nothing()),
                "actual Hole Wizard definition selects no live references")
        return data

    def point_world(self, point):
        sketch = self.get(point, "GetSketch")
        require(sketch is not None, "hole placement point has no real sketch")
        transform = self.get(self.get(sketch, "ModelToSketchTransform"), "Inverse")
        utility = self.get(self.app, "GetMathUtility")
        vector = self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, self.point(point))
        position = self.get(utility, "CreatePoint", vector)
        return tuple(float(x) for x in self.get(self.get(position, "MultiplyTransform", transform), "ArrayData"))

    def read_definition(self, feature, expected, case):
        data = self.definition(feature)
        try:
            keys = ("Type", "EndCondition", "Standard2", "FastenerType2", "FastenerSize",
                    "Diameter", "HoleDiameter", "ThruHoleDiameter", "ReverseDirection")
            if case["upper_m"]:
                keys += ("CounterBoreDiameter", "CounterBoreDepth")
            observed = {key: self.get(data, key) for key in keys}
            points = tuple(self.get(data, "GetSketchPoints") or ())
            count = int(self.get(data, "GetSketchPointCount"))
            observed["selected_positions_world_m"] = [self.point_world(point) for point in points]
            observed["placement_count"] = count
            self.rec.data["observed_wizard_definition"] = observed
            self.rec.flush()
        finally:
            self.get(data, "ReleaseSelectionAccess")
        require(count == len(points) == 1
                and dist(observed["selected_positions_world_m"][0], expected["point_m"]) <= 2e-8,
                "native position sketch moved from the exact selected face point")
        require((observed["Type"], observed["EndCondition"], observed["Standard2"],
                 observed["FastenerType2"], observed["FastenerSize"])
                == (case["observed_type"], 1, *case["catalog"][1:]) and not observed["ReverseDirection"],
                "native subtype, end, catalog identity or forward direction differs")
        self.rec.close_number("active HoleDiameter", observed["HoleDiameter"], expected["hole_diameter_m"])
        if case["upper_m"]:
            self.rec.close_number("active counterbore diameter", observed["CounterBoreDiameter"], expected["counterbore_diameter_m"])
            self.rec.close_number("active counterbore depth", observed["CounterBoreDepth"], expected["counterbore_depth_m"])
        return observed

    def edit(self, case):
        feature = self.feature(HOLE, "HoleWzd")
        data = self.definition(feature)
        modified = False
        try:
            self.set(data, case["edit_property"], case["edit_m"])
            modified = bool(self.get(feature, "ModifyDefinition", data, self.model, self.sw.nothing()))
            require(modified, "native selected feature definition rejected the independent edit")
        finally:
            if not modified:
                self.get(data, "ReleaseSelectionAccess")

    def displays(self, feature):
        results = []
        row = self.get(feature, "GetFirstDisplayDimension")
        while row is not None:
            require(len(results) < 20, "unexpected native dimension traversal length")
            dimension = self.get(row, "GetDimension2", 0)
            require(dimension is not None, "a native display has no retained dimension")
            results.append({"name": str(self.get(dimension, "FullName")).split("@")[:2],
                            "kind": int(self.get(row, "Type2")),
                            "amount": float(self.get(dimension, "SystemValue")),
                            "driven_state": int(self.get(dimension, "DrivenState")),
                            "read_only": bool(self.get(dimension, "ReadOnly"))})
            row = self.get(feature, "GetNextDisplayDimension", row)
        return results

    def shape(self, expected):
        body = self.body()
        faces = self.get(body, "GetFaces")
        cylinders = []
        for face in faces:
            surface = self.get(face, "GetSurface")
            if self.get(surface, "IsCylinder"):
                row = tuple(self.get(surface, "CylinderParams"))
                require(len(row) == 7 and abs(abs(row[5]) - 1) <= 1e-9
                        and dist(row[3:5], (0.0, 0.0)) <= 1e-9
                        and dist(row[:2], expected["point_m"][:2]) <= 2e-8,
                        "native bore has a different actual world axis")
                cylinders.append(row)
            else:
                require(self.get(surface, "IsPlane"), "unexpected nonplanar/noncylindrical source wall")
        self.rec.data["native_bore_cylinders"] = cylinders
        self.rec.flush()
        radii = sorted(row[6] for row in cylinders)
        wanted = sorted(expected["cylinder_radii_m"])
        require(1 <= len(radii) == len(wanted) <= 2 and len(faces) == (7 if len(radii) == 1 else 9),
                "native planar/cylindrical face incidence differs")
        for actual, target in zip(radii, wanted, strict=True):
            self.rec.close_number("physical cylinder radius", actual, target)
        vertices = [tuple(self.get(row, "GetPoint")) for row in self.get(body, "GetVertices")]
        require(all(sum(dist(value, vertex) <= 2e-8 for value in vertices) == 1
                    for vertex in expected["fixed_stock_corners_m"]),
                "the source body lost a true outer stock corner")
        low = tuple(min(point[axis] for point in vertices) for axis in range(3))
        high = tuple(max(point[axis] for point in vertices) for axis in range(3))
        require(dist(low, expected["minimum_m"]) <= 2e-8 and dist(high, expected["maximum_m"]) <= 2e-8,
                "the native body changed the exact stock extrema")
        mass = self.rec.call("measure exact source body", self.sw.mass, self.model)
        require(mass and "error" not in mass, "native hole solid mass properties are unavailable")
        self.rec.close_number("source solid SI volume", mass["volume"], expected["volume_m3"], absolute=1e-16)
        self.rec.close_number("source solid SI area", mass["area"], expected["area_m2"], absolute=1e-12)
        for actual, target in zip(mass["com"], expected["centroid_m"], strict=True):
            self.rec.close_number("source center of mass coordinate", actual, target)
        return {"cylinders": cylinders, "mass": mass, "body_count": 1,
                "faces": len(faces), "bounds_m": (low, high)}

    def observe(self, case, expected):
        from AuthorAssemblySources import feature_tree

        require(self.get(self.model, "ForceRebuild3", False), "native Hole Wizard source failed rebuild")
        extension = self.get(self.model, "Extension")
        require(self.get(extension, "GetWhatsWrongCount") == self.get(extension, "NeedsRebuild2") == 0,
                "native Hole Wizard source has rebuild diagnostics")
        feature = self.feature(HOLE, "HoleWzd")
        data = self.read_definition(feature, expected, case)
        tree = feature_tree(self, self.model)
        actual = {(row["name"], row["type"]) for row in tree if not row["suppressed"]}
        require({(STOCK, "Boss"), (HOLE, "HoleWzd")} <= actual, "live source feature tree changed")
        return {"wizard": data, "tree": tree, "display_dimensions": self.displays(feature),
                "geometry": self.shape(expected)}
