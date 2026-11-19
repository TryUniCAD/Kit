from __future__ import annotations

from itertools import combinations, product
from math import isclose, prod
from pathlib import Path

from AuthorCurves import CurveAuthor, digest, require


SOLID = 0
SHEET = 1
CHECK_BODY = 1
OBJECT_SAME = 1
IMPORTED = "Imported"


def box_expectation(case):
    x, y, z = case["face_center_m"]
    width, length, height = case["size_m"]
    bounds = ((x - width / 2, y - length / 2, z),
              (x + width / 2, y + length / 2, z + height))
    bits = tuple(product((0, 1), repeat=3))
    corners = tuple(tuple(bounds[bit][axis] for axis, bit in enumerate(corner)) for corner in bits)
    edges = tuple((i, j) for i, j in combinations(range(len(bits)), 2)
                  if sum(left != right for left, right in zip(bits[i], bits[j], strict=True)) == 1)
    faces = tuple(sorted(tuple(edge for edge in edges if all(bits[index][axis] == side for index in edge))
                         for axis in range(3) for side in (0, 1)))
    return {"corners": corners, "edges": edges, "faces": faces, "bounds": bounds,
            "volume": prod(case["size_m"]), "area": 2 * (width * length + width * height + length * height),
            "com": (x, y, z + height / 2)}


class ImportedBodyAuthor(CurveAuthor):
    def exact_object(self, left, right, label):
        require(left is not None and right is not None, f"missing identity: {label}")
        require(int(self.get(self.app, "IsSame", left, right)) == OBJECT_SAME, f"native identity differs: {label}")

    def body_topology(self, body, case, *, temporary):
        require(int(self.get(body, "GetType")) == SOLID, "import witness body is not solid")
        require(bool(self.get(body, "IsTemporaryBody")) is temporary, "unexpected temporary body state")
        target = box_expectation(case)

        def vertex_index(vertex):
            require(vertex is not None, "box edge has no endpoint")
            point = tuple(float(value) for value in self.get(self.typed(vertex, "Vertex"), "GetPoint"))
            matches = [index for index, expected in enumerate(target["corners"])
                       if len(point) == 3 and all(isclose(a, b, rel_tol=0, abs_tol=1e-9)
                                                  for a, b in zip(point, expected, strict=True))]
            self.rec.data.setdefault("corner_observations_m", []).append(point)
            require(len(matches) == 1, "native vertex is outside the independently predicted box corners")
            return matches[0]

        def edge_key(value):
            edge = self.typed(value, "Edge")
            curve = self.typed(self.get(edge, "GetCurve"), "Curve")
            require(bool(self.get(curve, "IsLine")), "modeler box edge is not a line")
            return tuple(sorted((vertex_index(self.get(edge, "GetStartVertex")),
                                 vertex_index(self.get(edge, "GetEndVertex")))))

        vertices = tuple(sorted(vertex_index(vertex) for vertex in self.get(body, "GetVertices") or ()))
        edges = tuple(sorted(edge_key(edge) for edge in self.get(body, "GetEdges") or ()))
        owners = tuple(self.typed(face, "Face2") for face in self.get(body, "GetFaces") or ())
        faces = []
        for face in owners:
            surface = self.typed(self.get(face, "GetSurface"), "Surface")
            require(bool(self.get(surface, "IsPlane")), "modeler box face is not planar")
            require(int(self.get(face, "GetLoopCount")) == 1, "modeler box face lacks its single loop")
            faces.append(tuple(sorted(edge_key(edge) for edge in self.get(face, "GetEdges") or ())))
        require(vertices == tuple(range(8)), "modeler box vertex inventory differs")
        require(edges == target["edges"], "modeler box edge incidence differs")
        require(tuple(sorted(faces)) == target["faces"], "modeler box face incidence differs")
        return {"vertices": len(vertices), "edges": len(edges), "faces": len(faces),
                "face_edge_incidence": sorted(faces), "analytic_bounds_m": target["bounds"]}, owners

    def persistent_reference(self, feature):
        raw = self.get(self.get(self.model, "Extension"), "GetPersistReference3", feature)
        require(raw is not None, "native imported feature lacks a persistent reference")
        data = bytes(raw)
        require(0 < len(data) <= 4096, "invalid persistent import reference length")
        return data.hex()

    def resolve_feature(self, token):
        kind = self.sw.pythoncom
        encoded = self.sw.VARIANT(kind.VT_ARRAY | kind.VT_UI1, list(bytes.fromhex(token)))
        error = self.sw.byref_long()
        feature = self.get(self.get(self.model, "Extension"), "GetObjectByPersistReference3", encoded, error)
        require(feature is not None and int(error.value) == 0, "saved import feature reference did not resolve")
        return self.typed(feature, "Feature")

    def author(self, controller, case):
        template = Path(self.rec.call("locate default part template", controller.template, "part"))
        require(template.is_file(), "default oracle part template is unavailable")
        self.rec.data["part_template_sha256"] = digest(template)
        self.model = self.rec.call("create blank part", controller.new_part)
        require(self.rec.data["part_template_sha256"] == digest(template), "part template changed during authoring")
        part = self.typed(self.model, "PartDoc")
        require(not any(self.get(part, "GetBodies2", kind, False) for kind in (SOLID, SHEET)),
                "default template already contains solid or sheet geometry")
        initial_tree = self.feature_tree(required_names=())
        require(not any(item["type"] == IMPORTED for item in initial_tree), "default template already has an import feature")
        self.rec.data["blank_tree"] = initial_tree
        values = (*case["face_center_m"], 0.0, 0.0, 1.0, *case["size_m"])
        kind = self.sw.pythoncom
        request = self.sw.VARIANT(kind.VT_ARRAY | kind.VT_R8, values)
        modeler = self.typed(self.get(self.app, "GetModeler"), "Modeler")
        solid = self.get(modeler, "CreateBodyFromBox3", request)
        require(solid is not None, "modeler did not create the temporary solid")
        solid = self.typed(solid, "Body2")
        topology, _ = self.body_topology(solid, case, temporary=True)
        self.rec.data.update(modeler_box_arguments_m=values, temporary_topology=topology)
        self.rec.flush()
        feature = self.get(part, "CreateFeatureFromBody3", solid, False, CHECK_BODY)
        require(feature is not None, "part did not create an imported feature")
        return self.typed(feature, "Feature")

    def rebuild(self):
        require(bool(self.get(self.model, "ForceRebuild3", False)), "imported source did not rebuild")

    def observe(self, feature, case):
        name = str(self.get(feature, "Name"))
        kind = str(self.get(feature, "GetTypeName2"))
        require(bool(name) and kind == IMPORTED, "native feature is not a named Imported feature")
        tree = self.feature_tree(required_names=(name,))
        require([row["name"] for row in tree if row["type"] == IMPORTED] == [name],
                "part must contain exactly one Imported feature")
        require(int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0,
                "native part has rebuild problems")
        part = self.typed(self.model, "PartDoc")
        solids = tuple(self.get(part, "GetBodies2", SOLID, False) or ())
        require(len(solids) == 1 and not self.get(part, "GetBodies2", SHEET, False),
                "part must expose one solid and zero sheet bodies")
        body = self.typed(solids[0], "Body2")
        topology, body_faces = self.body_topology(body, case, temporary=False)
        feature_faces = tuple(self.get(feature, "GetFaces") or ())
        require(len(feature_faces) == len(body_faces) == 6, "import face counts differ")
        for face in body_faces:
            self.exact_object(self.get(face, "GetFeature"), feature, "oldest owning import")
            self.exact_object(self.get(face, "GetBody"), body, "face owning the public solid")
        for value in feature_faces:
            face = self.typed(value, "Face2")
            self.exact_object(self.get(face, "GetBody"), body, "feature face owning the public solid")
        mass = self.rec.call("measure native part mass properties", self.sw.mass, self.model)
        require(mass and "error" not in mass, "native part mass properties are unavailable")
        target = box_expectation(case)
        self.rec.close_number("box volume", mass["volume"], target["volume"], absolute=1e-22)
        self.rec.close_number("box area", mass["area"], target["area"], absolute=1e-18)
        for axis, (actual, expected) in enumerate(zip(mass["com"], target["com"], strict=True)):
            self.rec.close_number(f"box centre coordinate {axis}", actual, expected, absolute=1e-11)
        return {"feature": {"name": name, "type": kind, "native_id": int(self.get(feature, "GetID"))},
                "body_name": str(self.get(body, "Name")), "body_count": 1, "topology": topology, "mass_si": mass,
                "feature_faces": len(feature_faces), "oldest_owner_face_count": len(body_faces), "tree": tree}
