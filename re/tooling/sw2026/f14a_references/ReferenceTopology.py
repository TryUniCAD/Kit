from itertools import product
from math import isclose

from BoxTopology import COUNTS, add_role, enclosing_faces, incidence, require_roles
from ReferencePacket import DRIVERS, require


INTERFACES = {"face": "Face2", "edge": "Edge", "vertex": "Vertex", "producer": "Feature"}
SELECTION_TYPES = {"face": "swSelFACES", "edge": "swSelEDGES", "vertex": "swSelVERTICES"}
STATION_TOLERANCE_M = 1e-10


def point_role(point, dimensions):
    matches = [tuple(flag for flag, bound in zip("01", (0.0, high), strict=True)
                     if isclose(float(value), bound, rel_tol=0.0, abs_tol=STATION_TOLERANCE_M))
               for value, high in zip(point, dimensions, strict=True)]
    require(all(len(bounds) == 1 for bounds in matches), "native vertex does not identify a unique box station")
    return "".join(bounds[0] for bounds in matches)


class Topology:
    def __init__(self, author, case, dimensions, enums):
        self.author = author
        self.model = author.model
        self.call = author.sw.invoke
        self.get = author.sw.cv
        self.same = enums["swObjectEquality"]["swObjectSame"]
        self.dimensions = tuple(dimensions[key] for key in DRIVERS)
        self.selection = self.cast(self.get(self.model, "SelectionManager"), "SelectionMgr")
        self.select_data = self.cast(self.get(self.selection, "CreateSelectData"), "SelectData")
        self.select_data.Mark = 0
        self.selection_enum = enums["swSelectType_e"]
        part = self.cast(self.model, "PartDoc")
        body_kinds = enums["swBodyType_e"]
        bodies = self.call(part, "GetBodies2", body_kinds["swSolidBody"], False) or ()
        require(len(bodies) == 1 and not self.call(part, "GetBodies2", body_kinds["swSheetBody"], False),
                "expected one native body and no additional sheet bodies")
        self.body = self.cast(bodies[0], "Body2")
        self.producer = self.cast(self.call(self.model, "FeatureByName", case["feature"]), "Feature")
        self.producer_name = str(self.get(self.producer, "Name"))
        self.producer_type = str(self.get(self.producer, "GetTypeName2"))
        require(self.producer_name == case["feature"], "native producer name changed")
        self.roles = {}
        self.objects = {}
        self.collect()

    def same_object(self, first, second):
        return int(self.call(self.author.app, "IsSame", first, second))

    def cast(self, value, interface):
        require(getattr(value, "_oleobj_", None) is not None, "native role has no COM dispatch object")
        target = getattr(self.author.interfaces, interface)
        target = getattr(target, "default_interface", target)
        return target(value._oleobj_.QueryInterface(target.CLSID, self.author.sw.pythoncom.IID_IDispatch))

    def compare(self, actual, expected, kind):
        return self.same_object(self.cast(actual, INTERFACES[kind]), expected)

    def vertex(self, vertex):
        typed = self.cast(vertex, "Vertex")
        return point_role(self.get(typed, "GetPoint"), self.dimensions)

    def edge(self, edge):
        typed = self.cast(edge, "Edge")
        require(bool(self.get(self.get(typed, "GetCurve"), "IsLine")), "native edge lacks a line carrier")
        corners = tuple(self.vertex(self.get(typed, name)) for name in ("GetStartVertex", "GetEndVertex"))
        return incidence(corners), corners

    def face(self, face):
        typed = self.cast(face, "Face2")
        require(bool(self.get(self.get(typed, "GetSurface"), "IsPlane")), "native face lacks a plane carrier")
        edges = [self.edge(edge) for edge in self.get(typed, "GetEdges") or ()]
        require(len(edges) == len({role for role, _ in edges}) == 4, "native box face must have four distinct sides")
        corners = set(end for _, points in edges for end in points)
        require(len(corners) == 4, "native box face must have four distinct corners")
        return incidence(corners), corners

    def classify(self, entity, kind):
        if kind == "vertex":
            role = self.vertex(entity)
            return role, (role,)
        return self.edge(entity) if kind == "edge" else self.face(entity)

    def face_ownership(self, face, role):
        body = self.cast(self.get(face, "GetBody"), "Body2")
        producer = self.cast(self.get(face, "GetFeature"), "Feature")
        require(self.same_object(body, self.body) == self.same_object(producer, self.producer) == self.same,
                "native face points to another body or producing feature")
        require(self.same_object(face, self.objects["face", role]) == self.same,
                "native face is not the unique live body boundary member")

    def collect(self):
        rows = {kind: {} for kind in COUNTS}
        for kind, method in (("face", "GetFaces"), ("edge", "GetEdges"), ("vertex", "GetVertices")):
            for item in self.get(self.body, method) or ():
                entity = self.cast(item, INTERFACES[kind])
                role, corners = self.classify(entity, kind)
                add_role(rows, kind, role, None, corners)
                self.objects[kind, role] = entity
        require_roles(rows)
        require(set(rows["vertex"]) == {"".join(value) for value in product("01", repeat=3)},
                "native box vertices do not cover the eight actual stations")
        feature_faces = self.get(self.producer, "GetFaces") or ()
        producer_roles = [self.resolved_role(face, "face") for face in feature_faces]
        require(len(producer_roles) == len(set(producer_roles)) == 6 and set(producer_roles) == set(rows["face"]),
                "native producer does not physically own all six boundary faces")
        for (kind, role), entity in self.objects.items():
            if kind != "face":
                self.resolved_role(entity, kind)
            self.roles[kind, role] = rows[kind][role]["touching_faces"]

    def resolved_role(self, entity, kind):
        typed = self.cast(entity, INTERFACES[kind])
        if kind == "producer":
            require(str(self.get(typed, "GetTypeName2")) == self.producer_type, "resolved producer has another feature type")
            return str(self.get(typed, "Name"))
        role, _ = self.classify(typed, kind)
        require((kind, role) in self.objects, "resolved native entity lies outside the measured box")
        if kind == "face":
            self.face_ownership(typed, role)
        else:
            method = "GetTwoAdjacentFaces2" if kind == "edge" else "GetAdjacentFaces"
            incident = [self.resolved_role(face, "face") for face in self.get(typed, method) or ()]
            require(sorted(incident) == sorted(enclosing_faces(role)), "actual native entity has different adjacent face owners")
        return role

    def select(self, expected, kind, row):
        self.clear()
        entity = self.cast(expected, "Entity")
        require(bool(self.call(entity, "Select4", False, self.select_data)), "native topology selection refused")
        require(int(self.call(self.selection, "GetSelectedObjectCount2", -1)) == 1, "native selection is ambiguous")
        row["selected_type"] = int(self.call(self.selection, "GetSelectedObjectType3", 1, -1))
        require(row["selected_type"] == self.selection_enum[SELECTION_TYPES[kind]], "native selection returned another entity kind")
        selected = self.cast(self.call(self.selection, "GetSelectedObject6", 1, -1), INTERFACES[kind])
        row["selected_object_equality"] = self.same_object(selected, expected)
        require(row["selected_object_equality"] == self.same, "native selection returned a different body entity")
        return selected

    def clear(self):
        self.call(self.model, "ClearSelection2", True)
