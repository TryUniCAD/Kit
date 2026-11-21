from contextlib import contextmanager

from AuthorCurves import CurveAuthor
from SweepModel import PATH, SECTION, require

SPEC = {
    SECTION: ("Right Plane", 0, "diameter_m", "swDiameterDimension", "AddDiameterDimension2"),
    PATH: ("Front Plane", 2, "arc_radius_m", "swRadialDimension", "AddRadialDimension2"),
}
ZERO = (0.0, 0.0, 0.0)
RELATIONS = {
    SECTION: (("swConstraintType_FIXED", ("center",)),),
    PATH: (("swConstraintType_FIXED", ("start",)), ("swConstraintType_VERTPOINTS", ("start", "center")),
           ("swConstraintType_HORIZPOINTS", ("center", "end"))),
}
POINT_GETTERS = {"center": "GetCenterPoint2", "start": "GetStartPoint2", "end": "GetEndPoint2"}


class SweepSketches(CurveAuthor):
    def __init__(self, app, rec, sw, constants):
        super().__init__(app, rec, sw)
        self.constants = constants

    @property
    def extension(self):
        return self.get(self.model, "Extension")

    @contextmanager
    def toggle(self, owner, key, enabled):
        option = self.constants[key]
        prior = bool(self.get(owner, "GetUserPreferenceToggle", option))
        try:
            self.get(owner, "SetUserPreferenceToggle", option, enabled)
            require(bool(self.get(owner, "GetUserPreferenceToggle", option)) == enabled, f"{key} changed unexpectedly")
            yield
        finally:
            self.get(owner, "SetUserPreferenceToggle", option, prior)
            require(bool(self.get(owner, "GetUserPreferenceToggle", option)) == prior, f"{key} was not restored")

    def vector_check(self, name, actual, expected, epsilon=1e-10):
        require(len(actual) == len(expected) == 3, f"{name} requires three coordinates")
        for index, (a, b) in enumerate(zip(actual, expected, strict=True)):
            self.rec.close_number(f"{name} xyz[{index}]", a, b, absolute=epsilon)

    def math_transform(self, point, frame, vector=False):
        utility = self.get(self.app, "GetMathUtility")
        arguments = self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, tuple(point))
        value = self.get(utility, "CreateVector" if vector else "CreatePoint", arguments)
        return [float(item) for item in self.get(self.get(value, "MultiplyTransform", frame), "ArrayData")]

    def sketch_frame(self, sketch, name):
        transform = self.get(sketch, "ModelToSketchTransform")
        inverse = self.get(transform, "Inverse")
        origin = self.math_transform(ZERO, inverse)
        normal = self.math_transform((0, 0, 1), inverse, vector=True)
        self.vector_check(f"{name} origin", origin, ZERO)
        self.vector_check(f"{name} plane normal", [abs(item) for item in normal],
                          [int(index == SPEC[name][1]) for index in range(3)])
        if name == PATH:
            for axis in range(3):
                unit = [int(index == axis) for index in range(3)]
                self.vector_check(f"{name} canonical basis {axis}", self.math_transform(unit, inverse, vector=True), unit)
        return inverse, {"origin_m": origin, "normal": normal}

    def feature_sketch(self, feature, expected):
        feature = self.typed(feature, "Feature")
        require(self.get(feature, "Name") == expected and self.get(feature, "GetTypeName2") == "ProfileFeature",
                f"definition selection is not the expected named 2D sketch {expected}")
        return self.typed(self.get(feature, "GetSpecificFeature2"), "Sketch")

    def points(self, arc, name):
        roles = ("center",) if name == SECTION else ("start", "center", "end")
        return {role: self.typed(self.get(arc, POINT_GETTERS[role]), "SketchPoint") for role in roles}

    def relation_key(self, kind, points):
        ids = [tuple(self.entity_binding(point, "point")["id"]) for point in points]
        require(len(set(ids)) == len(ids), "relation uses the same native point twice")
        return kind, tuple(sorted(ids))

    def add_relations(self, sketch, arc, name):
        manager = self.get(sketch, "RelationManager")
        points = self.points(arc, name)
        for relation, roles in RELATIONS[name]:
            entries = [points[role] for role in roles]
            kind = self.constants[relation]
            native = self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_DISPATCH, entries)
            value = self.get(manager, "AddRelation", native, kind)
            require(value is not None and self.read_relation(value) == self.relation_key(kind, entries),
                    f"native {name} did not create the requested {relation} relation")

    def read_relation(self, relation):
        kind = int(self.get(relation, "GetRelationType"))
        supported = {self.constants[key] for values in RELATIONS.values() for key, _ in values}
        require(kind in supported, f"unsupported sketch relation type {kind}")
        entities = self.get(relation, "GetEntities") or ()
        require(len(entities) == int(self.get(relation, "GetEntitiesCount"))
                and not self.get(relation, "Suppressed"), "native sketch relation is incomplete or suppressed")
        return self.relation_key(kind, entities)

    def inspect_relations(self, sketch, name, points):
        manager = self.get(sketch, "RelationManager")
        expected = sorted(self.relation_key(self.constants[key], [points[role] for role in roles])
                          for key, roles in RELATIONS[name])
        actual = sorted(self.read_relation(item) for item in self.get(manager, "GetRelations", self.constants["swAll"]) or ())
        require(actual == expected, f"{name} has unexpected or missing actual point relation owners")
        for key in ("swDangling", "swOverDefining", "swBroken"):
            require(int(self.get(manager, "GetRelationsCount", self.constants[key])) == 0, f"{name} has {key} relations")
        return actual

    def set_driver(self, dimension, value):
        status = int(self.get(dimension, "SetSystemValue3", value, self.constants["swSetValue_InThisConfiguration"],
                              self.sw.nothing()))
        require(status == self.constants["swSetValue_Successful"], f"native driving dimension setter returned {status}")
        self.rec.close_number("the native dimension accepted its SI driving value", self.get(dimension, "SystemValue"), value)

    def create_dimension(self, segment, name, plan):
        self.get(self.model, "ClearSelection2", True)
        require(self.get(segment, "Select4", False, self.sw.nothing()), "actual section or path segment selection failed")
        _, _, key, _, method = SPEC[name]
        label = (0.0, 0.012, 0.012) if name == SECTION else (0.015, 0.004, 0.0)
        display = self.typed(self.get(self.model, method, *label), "DisplayDimension")
        dimension = self.typed(self.get(display, "GetDimension2", 0), "Dimension")
        require(int(self.get(dimension, "DrivenState")) == self.constants["swDimensionDriving"]
                and not self.get(dimension, "ReadOnly"), "native sketch did not create a live driving dimension")
        self.set_driver(dimension, plan[key])
        self.get(self.model, "ClearSelection2", True)

    def create_sketch(self, name, plan):
        plane = SPEC[name][0]
        self.get(self.model, "ClearSelection2", True)
        require(self.get(self.extension, "SelectByID2", plane, "PLANE", *ZERO, False, 0, self.sw.nothing(), 0),
                f"cannot select canonical stock plane {plane}")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        sketch = self.typed(self.get(manager, "ActiveSketch"), "Sketch")
        self.sketch_frame(sketch, name)
        self.set(manager, "AddToDB", True)
        try:
            if name == SECTION:
                segment = self.get(manager, "CreateCircleByRadius", *ZERO, plan["diameter_m"] / 2)
            else:
                points = plan["path"]
                segment = self.get(manager, "CreateArc", *points["center"], *points["start"], *points["end"], 1)
        finally:
            self.set(manager, "AddToDB", False)
        arc = self.typed(segment, "SketchArc")
        self.add_relations(sketch, arc, name)
        self.create_dimension(segment, name, plan)
        self.get(manager, "InsertSketch", True)
        require(self.get(manager, "ActiveSketch") is None, f"{name} remains unexpectedly in edit mode")
        feature = self.get(self.model, "FeatureByPositionReverse", 0)
        require(feature is not None and self.get(feature, "GetTypeName2") == "ProfileFeature"
                and self.get(feature, "Name") not in (SECTION, PATH), "latest feature is not the newly authored sketch")
        self.set(feature, "Name", name)
        self.inspect_sketch(feature, name, plan)

    def inspect_sketch(self, feature, name, plan):
        sketch = self.feature_sketch(feature, name)
        status = int(self.get(sketch, "GetConstrainedStatus"))
        require(status == 3, f"{name} is not fully constrained (native status {status})")
        inverse, frame = self.sketch_frame(sketch, name)
        segments = self.get(sketch, "GetSketchSegments") or ()
        require(len(segments) == 1 and self.get(segments[0], "GetType") == self.constants["swSketchARC"]
                and not self.get(segments[0], "ConstructionGeometry"), "wrong physical segment inventory")
        arc = self.typed(segments[0], "SketchArc")
        circle = bool(self.get(arc, "IsCircle"))
        require(circle == (name == SECTION), "native section and path have the wrong circular closure")
        radius = plan["diameter_m"] / 2 if circle else plan["arc_radius_m"]
        self.rec.close_number(f"{name} segment radius", self.get(arc, "GetRadius"), radius)
        points = self.points(arc, name)
        point_positions = {role: self.math_transform(self.point(point), inverse) for role, point in points.items()}
        for role, xyz in point_positions.items():
            self.vector_check(f"{name} {role}", xyz, ZERO if circle else plan["path"][role])
        if not circle:
            require(int(self.get(arc, "GetRotationDir")) == 1, "actual Front path is not counterclockwise")
            self.rec.close_number("explicit quarter-arc length", self.get(segments[0], "GetLength"), plan["arc_length_m"])
        return {"frame": frame, "segment": self.entity_binding(segments[0], "segment"), "points_m": point_positions,
                "relations": self.inspect_relations(sketch, name, points), "fully_constrained": status, "circle": circle}

    def driving_dimension(self, feature, name, plan):
        inventory = []
        with self.toggle(self.model, "swDisplayFeatureDimensions", True):
            display = self.get(feature, "GetFirstDisplayDimension")
            while display is not None:
                require(len(inventory) < 16, f"{name} native dimension inventory exceeds scope")
                dimension = self.typed(self.get(display, "GetDimension2", 0), "Dimension")
                row = {"name": str(self.get(dimension, "FullName")), "value_m": float(self.get(dimension, "SystemValue")),
                       "display_kind": int(self.get(display, "Type2")), "driven": int(self.get(dimension, "DrivenState")),
                       "read_only": bool(self.get(dimension, "ReadOnly"))}
                inventory.append((row, dimension))
                display = self.get(feature, "GetNextDisplayDimension", display)
        self.rec.data[f"last_{name}_dimensions"] = [row for row, _ in inventory]
        self.rec.flush()
        require(len(inventory) == 1, f"{name} does not own exactly one display dimension")
        row, dimension = inventory[0]
        key, kind, _ = SPEC[name][2:]
        parts = row["name"].split("@")
        require(len(parts) >= 2 and parts[1] == name and parts[0].startswith("D") and parts[0][1:].isdigit()
                and row["display_kind"] == self.constants[kind]
                and row["driven"] == self.constants["swDimensionDriving"] and not row["read_only"],
                f"{name} lacks the expected driving dimension owner and type")
        self.rec.close_number(f"{name} {key}", row["value_m"], plan[key])
        return row, dimension
