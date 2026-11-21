from math import dist, fsum, isfinite

import Swapp
from AuthorCurves import require
from AuthorPatternEnvelope import PatternEnvelopeAuthor
from ObliqueCylinderApi import LIBRARIES


PROPERTIES = {"IRefPlane": "BoundingBox", "IMathPoint": "ArrayData"}
TOLERANCE = 5e-9


def bounds_metadata(angle):
    pythoncom = Swapp.pythoncom
    pythoncom.CoInitialize()
    try:
        library = pythoncom.LoadRegTypeLib(LIBRARIES["sldworks"], 34, 0, 0)
        require(tuple(library.GetLibAttr()[3:5]) == (34, 0)
                and str(library.GetLibAttr()[0]) == angle["libraries"]["sldworks"]["guid"],
                "display bounds require the same registered version-34 model library")
        matches = {}
        for index in range(library.GetTypeInfoCount()):
            info = library.GetTypeInfo(index)
            kind = info.GetDocumentation(-1)[0]
            if kind not in PROPERTIES:
                continue
            attr = info.GetTypeAttr()
            require(kind not in matches and str(attr[0]) == angle["interfaces"][kind]["guid"],
                    "display bounds declared a different interface")
            getters = []
            for ordinal in range(attr.cFuncs):
                member = info.GetFuncDesc(ordinal)
                names = list(info.GetNames(member.memid))
                if names[:1] == [PROPERTIES[kind]] and member.invkind == pythoncom.DISPATCH_PROPERTYGET:
                    getters.append((member, names))
            require(len(getters) == 1, "display observation needs one exact registered property getter")
            member, names = getters[0]
            require(names == [PROPERTIES[kind]] and not member.args and member.rettype[0] == pythoncom.VT_VARIANT,
                    "display observation requires a no-argument Automation VARIANT getter")
            matches[kind] = {"guid": str(attr[0]), "property": names[0], "dispid": member.memid,
                             "invoke": member.invkind, "arguments": 0, "return_vartype": member.rettype[0]}
        require(set(matches) == set(PROPERTIES), "one registered display getter is missing")
        return matches
    finally:
        pythoncom.CoUninitialize()


class PatternDatumHeightAuthor(PatternEnvelopeAuthor):
    def __init__(self, application, recorder, api, spec):
        super().__init__(application, recorder, api["angle"], spec)
        self.display = api["datum_bounds"]

    def display_get(self, value, interface):
        binding = self.display[interface]
        return self.rec.call("declared " + interface + "." + binding["property"], value._oleobj_.Invoke,
                             binding["dispid"], 0, binding["invoke"], True, parameters=binding)

    def record_display(self, stage):
        feature, _ = self.direction_plane(self.case)
        geometry = self.datum_author.plane_geometry(feature)
        direction = self.spec["direction_datum"]
        wanted = direction["required_signed_normal"]
        normal = geometry["normal"]
        require(dist(geometry["origin_m"], direction["origin_m"]) <= 1e-10
                and min(dist(normal, wanted), dist(normal, [-x for x in wanted])) <= 1e-10,
                "display box belongs to a different actual datum frame")
        specific = self.get(feature, "GetSpecificFeature2")
        plane = self.datum_author.declared_interface(specific, "IRefPlane")
        corners = self.display_get(plane, "IRefPlane")
        require(isinstance(corners, (tuple, list)) and len(corners) == 2,
                "actual datum BoundingBox requires two MathPoint coordinates")
        points = []
        for corner in corners:
            point = self.datum_author.declared_interface(Swapp.wc.Dispatch(corner), "IMathPoint")
            position = self.display_get(point, "IMathPoint")
            require(isinstance(position, (tuple, list)) and len(position) == 3
                    and all(type(x) in (int, float) and isfinite(x) for x in position),
                    "plane display corner is not a finite point in the model")
            points.append(list(position))
        delta = [b - a for a, b in zip(*points, strict=True)]
        u, v = geometry["transform"][:3], geometry["transform"][3:6]
        require(all(abs(fsum(a * b for a, b in zip(normal, point, strict=True))) <= TOLERANCE for point in points)
                and min(abs(fsum(a * b for a, b in zip(axis, delta, strict=True))) for axis in (u, v)) > TOLERANCE,
                "measured display points do not span a model-space diagonal on the selected datum")
        checkpoint = {"datum": str(self.get(feature, "Name")),
                      "feature_reference": self.persistent(feature, "actual display plane"),
                      "geometry_reference": self.persistent(plane, "actual display plane geometry"),
                      "model_diagonal_m": points,
                      "midpoint_m": [(a + b) / 2 for a, b in zip(*points, strict=True)],
                      "frame": geometry}
        stages = self.rec.data.setdefault("datum_display_checkpoints", {})
        require(stage not in stages, "display stage was already observed")
        stages[stage] = checkpoint
        self.rec.flush()

    def create_pattern(self, seed):
        self.record_display("preselection")
        super().create_pattern(seed)
        self.record_display("created")

    def envelope_state(self, label, arm_index):
        result = super().envelope_state(label, arm_index)
        self.record_display("rebuilt" if label == "authored" else "reopened")
        return result
