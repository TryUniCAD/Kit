from __future__ import annotations

from itertools import product
from math import isclose

from AuthorCurves import require
from AuthorRectangleAnchors import RectangleAuthor


PLANE = "Top Plane"
SKETCH = "AdditiveBox Profile"
BOSS = "AdditiveBox"
BODY = "Body"
DRIVERS = ("Length", "Width", "Height")
OWNERS = (SKETCH, SKETCH, BOSS)
PARAMETERS = tuple(f"{name}@{owner}" for name, owner in zip(DRIVERS, OWNERS, strict=True))


def corners(length, width):
    return ((0.0, 0.0), (length, 0.0), (length, -width), (0.0, -width))


def close_point(observed, expected):
    return len(observed) == len(expected) and all(
        isclose(value, target, rel_tol=2e-7, abs_tol=1e-10)
        for value, target in zip(observed, expected, strict=True)
    )


class AttachedTopBoxAuthor(RectangleAuthor):
    def world_point(self, sketch_point):
        utility = self.get(self.app, "GetMathUtility")
        inverse = self.get(self.get(self.sketch, "ModelToSketchTransform"), "Inverse")
        vector = self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, sketch_point)
        value = self.get(utility, "CreatePoint", vector)
        return tuple(float(item) for item in self.get(self.get(value, "MultiplyTransform", inverse), "ArrayData"))

    def frame(self):
        expected = {
            "origin": (0.0, 0.0, 0.0),
            "u": (1.0, 0.0, 0.0),
            "v": (0.0, 0.0, -1.0),
            "normal": (0.0, 1.0, 0.0),
        }
        actual = {
            "origin": self.world_point((0.0, 0.0, 0.0)),
            "u": self.world_point((1.0, 0.0, 0.0)),
            "v": self.world_point((0.0, 1.0, 0.0)),
            "normal": self.world_point((0.0, 0.0, 1.0)),
        }
        self.rec.data["observed_top_frame"] = actual
        self.rec.flush()
        for role, wanted in expected.items():
            require(close_point(actual[role], wanted), f"unexpected native Top-plane {role}")
        return actual

    def verify_profile(self, length, width):
        vertices = corners(length, width)
        edges = list(zip(vertices, (*vertices[1:], vertices[0]), strict=True))
        geometry = self.geometry()
        require(len(geometry) == 4 and all(row["kind"] == "line" and not row["construction"] for row in geometry),
                "signed Top rectangle must contain four ordinary line edges")
        for segment in geometry:
            matches = [
                edge for edge in edges
                if (close_point(segment["start"], edge[0]) and close_point(segment["end"], edge[1]))
                or (close_point(segment["start"], edge[1]) and close_point(segment["end"], edge[0]))
            ]
            require(len(matches) == 1, "rectangle creation or rebuild failed to preserve the signed local contour")
            edges.remove(matches[0])
        return geometry

    def dimension_edge(self, segments, axis, location, value):
        perpendicular = 1 - axis
        selected = []
        for segment in segments:
            line = self.typed(segment, "SketchLine")
            start, end = (self.point(self.get(line, member)) for member in ("GetStartPoint2", "GetEndPoint2"))
            if isclose(start[perpendicular], 0, abs_tol=1e-10) and isclose(end[perpendicular], 0, abs_tol=1e-10):
                if not isclose(start[axis], end[axis], abs_tol=1e-10):
                    selected.append(segment)
        require(len(selected) == 1, "ambiguous rectangle dimension edge at origin")
        self.get(self.model, "ClearSelection2", True)
        require(self.get(selected[0], "Select4", False, self.sw.nothing()), "rectangle dimension edge selection failed")
        require(self.get(self.get(self.model, "SelectionManager"), "GetSelectedObjectCount2", -1) == 1,
                "dimension selection contains an unexpected entity")
        display = self.get(self.model, "AddDimension2", *self.world_point((*location, 0.0)))
        require(display is not None, "signed Top rectangle display dimension was not created")
        dimension = self.get(display, "GetDimension2", 0)
        require(dimension is not None and int(self.get(dimension, "DrivenState")) == 2,
                "signed Top rectangle dimension is not driving")
        self.rec.close_number("new positive rectangle driver", self.get(dimension, "SystemValue"), value)
        self.get(self.model, "ClearSelection2", True)
        return dimension

    def verify_origin_coincidence(self, geometry):
        corners_at_origin = {
            tuple(segment["point_bindings"][role]["id"])
            for segment in geometry
            for role in ("start", "end")
            if close_point(segment[role], (0.0, 0.0))
        }
        require(len(corners_at_origin) == 1, "signed Top rectangle has no unique local origin corner")
        extension = self.get(self.model, "Extension")
        self.get(self.model, "ClearSelection2", True)
        require(self.get(extension, "SelectByID2", "Point1@Origin", "EXTSKETCHPOINT",
                         0.0, 0.0, 0.0, False, 0, self.sw.nothing(), 0), "model origin readback selection failed")
        try:
            selected = self.get(self.model, "SelectionManager")
            origin = self.typed(self.get(selected, "GetSelectedObject6", 1, -1), "SketchPoint")
            require(close_point(self.point(origin), (0.0, 0.0, 0.0)), "actual model origin is not at zero")
            manager = self.get(self.sketch, "RelationManager")
            matches = []
            for relation in self.get(manager, "GetRelations", 0) or ():
                if int(self.get(relation, "GetRelationType")) != 9 or self.get(relation, "Suppressed"):
                    continue
                related = list(self.get(relation, "GetEntities") or ())
                if len(related) != 2 or tuple(self.get(relation, "GetEntitiesType") or ()) != (2, 2):
                    continue
                points = []
                for item in related:
                    point = self.typed(item, "SketchPoint")
                    owner = self.get(point, "GetSketch")
                    points.append({
                        "id": tuple(self.get(point, "GetID")),
                        "type": int(self.get(point, "Type")),
                        "position_m": self.point(point),
                        "profile_owned": owner is not None and int(self.get(self.app, "IsSame", owner, self.sketch)) == 1,
                        "same_as_selected_model_origin": int(self.get(self.app, "IsSame", origin, point)),
                    })
                local, proxy = sorted(points, key=lambda row: row["type"])
                if (local["type"] == 0 and proxy["type"] == 10 and local["id"] in corners_at_origin
                    and all(row["profile_owned"] and close_point(row["position_m"], (0.0, 0.0, 0.0))
                            for row in points)):
                    matches.append({"corner_id": local["id"], "external_point_proxy_id": proxy["id"],
                                    "model_origin_id": tuple(self.get(origin, "GetID")), "points": points})
            require(len(matches) == 1, "native sketch lacks one origin coincidence with a profile-owned external proxy")
            self.rec.data["origin_relation"] = matches[0]
            self.rec.flush()
            return matches[0]
        finally:
            self.get(self.model, "ClearSelection2", True)

    def build(self, controller, dimensions):
        length, width, height = dimensions
        self.model = self.rec.call("create native attached Top box source", controller.new_part)
        extension = self.get(self.model, "Extension")
        self.get(self.model, "ClearSelection2", True)
        require(self.get(extension, "SelectByID2", PLANE, "PLANE", 0.0, 0.0, 0.0, False, 0, self.sw.nothing(), 0),
                "native Top Plane selection failed")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        self.sketch = self.get(manager, "ActiveSketch")
        require(self.sketch is not None and not self.get(manager, "AddToDB"), "native interactive sketch creation unavailable")
        self.frame()
        segments = list(self.get(manager, "CreateCornerRectangle", 0.0, 0.0, 0.0, length, -width, 0.0) or ())
        require(len(segments) == 4, "rectangle authoring did not return four edges")
        self.verify_profile(length, width)
        first = self.dimension_edge(segments, 0, (length / 2, width * 0.3), length)
        second = self.dimension_edge(segments, 1, (-length * 0.3, -width / 2), width)
        if int(self.get(self.sketch, "GetConstrainedStatus")) == 2:
            self.anchor(segments, extension)
        require(int(self.get(self.sketch, "GetConstrainedStatus")) == 3, "signed Top rectangle is not fully constrained")
        self.verify_profile(length, width)
        self.get(manager, "InsertSketch", True)
        feature = self.created_sketch_feature()
        self.set(feature, "Name", SKETCH)
        self.get(self.model, "ClearSelection2", True)
        require(self.get(feature, "Select2", False, 0), "native signed rectangle selection failed")
        boss = self.get(self.get(self.model, "FeatureManager"), "FeatureExtrusion3",
                        True, False, True, 0, 0, height, 0.0, False, False, False, False,
                        0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        require(boss is not None, "native reversed blind boss was not created")
        self.set(boss, "Name", BOSS)
        display = self.get(boss, "GetFirstDisplayDimension")
        require(display is not None, "reversed blind boss has no depth display")
        third = self.get(display, "GetDimension2", 0)
        require(third is not None, "reversed blind boss depth display has no dimension")
        for label, dimension in zip(DRIVERS, (first, second, third), strict=True):
            self.set(dimension, "Name", label)
        bodies = tuple(self.get(self.model, "GetBodies2", 0, False) or ())
        require(len(bodies) == 1, "named box source requires one initial solid")
        self.set(bodies[0], "Name", BODY)
        self.get(self.get(self.model, "FeatureManager"), "UpdateFeatureTree")

    def parents(self, feature, parent, kind):
        parents = self.get(feature, "GetParents") or ()
        names = [{"name": str(self.get(item, "Name")), "kind": str(self.get(item, "GetTypeName2"))}
                 for item in parents]
        require(sum(row == {"name": parent, "kind": kind} for row in names) == 1,
                "native feature has lost its actual parent")
        return names

    def solid(self, length, width, height):
        bodies = tuple(self.get(self.model, "GetBodies2", 0, False) or ())
        require(len(bodies) == 1, "signed Top source must rebuild to one solid")
        body, = bodies
        body_name = str(self.get(body, "Name"))
        require(body_name == BODY, "native Body name did not persist")
        vertices = tuple(self.get(body, "GetVertices") or ())
        topology = (len(vertices), len(self.get(body, "GetEdges") or ()), len(self.get(body, "GetFaces") or ()))
        require(topology == (8, 12, 6), "native signed box has unexpected topology")
        points = [tuple(float(value) for value in self.get(vertex, "GetPoint")) for vertex in vertices]
        remaining = list(points)
        for expected in product((0.0, length), (-height, 0.0), (0.0, width)):
            matches = [point for point in remaining if close_point(point, expected)]
            require(len(matches) == 1, "body corners do not match the independent F14c world orientation")
            remaining.remove(matches[0])
            for value, target in zip(matches[0], expected, strict=True):
                self.rec.close_number("body vertex coordinate", value, target, absolute=1e-10)
        mass = self.rec.call("measure signed Top box", self.sw.mass, self.model)
        require(isinstance(mass, dict) and "error" not in mass, "native mass properties unavailable")
        self.rec.close_number("solid volume", mass["volume"], length * width * height, absolute=1e-19)
        self.rec.close_number("solid area", mass["area"], 2 * (length * width + length * height + width * height), absolute=1e-16)
        for value, target in zip(mass["com"], (length / 2, -height / 2, width / 2), strict=True):
            self.rec.close_number("solid centre of mass coordinate", value, target, absolute=1e-10)
        return {"body_count": 1, "name": body_name, "topology": topology, "vertices": points, "mass": mass}

    def snapshot(self, dimensions):
        length, width, height = dimensions
        require(self.get(self.model, "ForceRebuild3", False), "signed Top model did not rebuild")
        require(int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0, "native source rebuild has diagnostics")
        feature = self.get(self.model, "FeatureByName", SKETCH)
        boss = self.get(self.model, "FeatureByName", BOSS)
        require(feature is not None and boss is not None, "native source authoring history is missing")
        self.sketch = self.get(feature, "GetSpecificFeature2")
        require(int(self.get(self.sketch, "GetConstrainedStatus")) == 3, "signed Top rectangle lost full constraint")
        frame = self.frame()
        geometry = self.verify_profile(length, width)
        anchor = self.verify_origin_coincidence(geometry)
        reference = self.parents(feature, PLANE, "RefPlane")
        profile_owner = self.parents(boss, SKETCH, "ProfileFeature")
        definition = self.get(boss, "GetDefinition")
        require(definition is not None, "reversed blind boss definition is missing")
        direction = {
            "end": int(self.get(definition, "GetEndCondition", True)),
            "from": int(self.get(definition, "FromType")),
            "reverse": bool(self.get(definition, "ReverseDirection")),
            "both_directions": bool(self.get(definition, "BothDirections")),
            "draft": bool(self.get(definition, "GetDraftWhileExtruding", True)),
        }
        require(direction == {"end": 0, "from": 0, "reverse": True, "both_directions": False, "draft": False},
                "native extrusion direction or blind end policy differs")
        self.rec.close_number("feature definition positive depth", self.get(definition, "GetDepth", True), height)
        drivers = {}
        for parameter, value in zip(PARAMETERS, dimensions, strict=True):
            dimension = self.get(self.model, "Parameter", parameter)
            require(dimension is not None and int(self.get(dimension, "DrivenState")) == 2 and not self.get(dimension, "ReadOnly"),
                    f"native source dimension is not an editable driver: {parameter}")
            require("@".join(str(self.get(dimension, "FullName")).split("@")[:2]) == parameter,
                    "named native source driver belongs to another feature")
            drivers[parameter] = float(self.get(dimension, "SystemValue"))
            require(drivers[parameter] > 0, "native source uses a negative driving length")
            self.rec.close_number(parameter, drivers[parameter], value)
        return {"frame": frame, "sketch": geometry, "relations": self.relation_graph(), "origin_relation": anchor,
                "top_parent": reference,
                "boss_parent": profile_owner, "end_condition": direction, "drivers_m": drivers,
                "solid": self.solid(length, width, height),
                "tree": self.feature_tree(required_names=(PLANE, SKETCH, BOSS))}
