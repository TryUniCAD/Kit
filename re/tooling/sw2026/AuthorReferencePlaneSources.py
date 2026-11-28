from __future__ import annotations

import math
import os

from AuthorCurves import CurveAuthor, require
from ReferencePlaneSourcePlan import BASE_NAMES, BOSS, PLANE, SKETCH, geometry


LIBRARY = "{83A33D31-27C5-11CE-BFD4-00400513BB57}"
CONSTANTS = "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}"
INSERT_ARGUMENTS = ("FirstConstraint", "FirstConstraintAngleOrDistance", "SecondConstraint", "SecondConstraintAngleOrDistance", "ThirdConstraint", "ThirdConstraintAngleOrDistance")


def metadata():
    require(os.name == "nt", "registered reference-plane API metadata is inspected only in the Windows guest")
    import Swapp

    Swapp.pythoncom.CoInitialize()
    try:
        libraries = {name: Swapp.pythoncom.LoadRegTypeLib(identity, 34, 0, 0) for name, identity in (("sldworks", LIBRARY), ("swconst", CONSTANTS))}
        require(all(tuple(value.GetLibAttr()[3:5]) == (34, 0) for value in libraries.values()), "reference-plane type libraries must be major 34 minor 0")
        members, enums = {}, {}
        for library_name, library in libraries.items():
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                wanted = {
                    "IFeatureManager": ("InsertRefPlane",),
                    "IRefPlaneFeatureData": ("Constraint", "Reference", "AngleOrDistance", "Type", "Type2", "Distance", "Angle", "ReversedReferenceDirection", "AccessSelections", "ReleaseSelectionAccess"),
                    "IRefPlane": ("Transform",),
                    "IFeature": ("Name", "GetTypeName2", "GetFirstDisplayDimension", "GetNextDisplayDimension", "GetSpecificFeature2"),
                    "IDimension": ("FullName", "SystemValue", "DrivenState", "ReadOnly"),
                    "IDisplayDimension": ("GetDimension2", "Type2"),
                    "ISldWorks": ("IsSame",),
                }
                if name in wanted:
                    selected = []
                    for ordinal in range(info.GetTypeAttr().cFuncs):
                        descriptor = info.GetFuncDesc(ordinal)
                        names = tuple(info.GetNames(descriptor.memid))
                        keep = names and names[0] in wanted[name]
                        if keep:
                            selected.append({"names": list(names), "member_id": descriptor.memid, "invoke_kind": descriptor.invkind,
                                             "arguments": repr(descriptor.args), "return_type": repr(descriptor.rettype)})
                    members[name] = {"guid": str(info.GetTypeAttr()[0]), "members": selected}
                if library_name == "swconst" and name in ("swRefPlaneReferenceConstraints_e", "swRefPlaneReferenceIndex_e", "swRefPlaneType_e", "swObjectEquality", "swDimensionType_e"):
                    values = {}
                    for ordinal in range(info.GetTypeAttr().cVars):
                        constant = info.GetVarDesc(ordinal)
                        require(type(constant.value) is int, "reference-plane enum is not an integer declaration")
                        values[info.GetNames(constant.memid)[0]] = constant.value
                    enums[name] = values
        signature, = members["IFeatureManager"]["members"]
        require(tuple(name.casefold() for name in signature["names"][1:]) == tuple(name.casefold() for name in INSERT_ARGUMENTS),
                "registered InsertRefPlane argument order differs")
        constraints = enums["swRefPlaneReferenceConstraints_e"]
        require(constraints["swRefPlaneReferenceConstraint_Distance"] == 8 and constraints["swRefPlaneReferenceConstraint_Angle"] == 16 and
                constraints["swRefPlaneReferenceConstraint_OptionFlip"] == 256, "registered reference-plane constraint codes differ")
        for name in ("Constraint", "Reference", "AngleOrDistance"):
            require(any(row["names"][0] == name and row["invoke_kind"] == 2 for row in members["IRefPlaneFeatureData"]["members"]), "indexed reference-plane property is unavailable")
        require(enums["swObjectEquality"]["swObjectSame"] == 1 and enums["swObjectEquality"]["swObjectNotSame"] == 0 and
                enums["swObjectEquality"]["swObjectUnsupported"] == 2, "registered native object identity states differ")
        require(all(name in enums["swDimensionType_e"] for name in ("swRadialDimension", "swLinearDimension")), "registered radial or linear display dimension kind is absent")
        for interface, names in wanted.items():
            require(interface in members and all(any(row["names"][0] == name for row in members[interface]["members"]) for name in names),
                    "registered dimension ownership interface is incomplete")
        return {"schema": "kit.sw2026.reference-plane-api-metadata.v1", "libraries": {name: {
                    "guid": str(value.GetLibAttr()[0]), "major": value.GetLibAttr()[3], "minor": value.GetLibAttr()[4]} for name, value in libraries.items()},
                "interfaces": members, "enums": enums, "native_processes_started": 0, "passed": True}
    finally:
        Swapp.pythoncom.CoUninitialize()


class PlaneAuthor(CurveAuthor):
    def __init__(self, application, recorder, modules, api):
        super().__init__(application, recorder, modules)
        self.api = api

    def top_features(self):
        result = []
        feature = self.get(self.model, "FirstFeature")
        while feature is not None:
            require(len(result) < 256, "source feature traversal exceeded its declared small profile")
            result.append((feature, str(self.get(feature, "Name")), str(self.get(feature, "GetTypeName2"))))
            feature = self.get(feature, "GetNextFeature")
        return result

    def indexed(self, definition, name, index):
        member, = [row for row in self.api["interfaces"]["IRefPlaneFeatureData"]["members"] if row["names"][0] == name and row["invoke_kind"] == 2]
        return self.rec.call("get indexed plane " + name, definition._oleobj_.Invoke, member["member_id"], 0, member["invoke_kind"], True, index,
                             parameters={"property": name, "member_id": member["member_id"], "reference_index": index, "invocation_kind": member["invoke_kind"]})

    def declared_interface(self, value, name):
        identity = self.sw.pythoncom.MakeIID(self.api["interfaces"][name]["guid"])
        proxy = self.rec.call("QueryInterface " + name, value._oleobj_.QueryInterface, identity, self.sw.pythoncom.IID_IDispatch,
                              parameters={"interface": name, "iid": str(identity)})
        return self.sw.wc.Dispatch(proxy)

    def world_point(self, point):
        utility = self.get(self.app, "GetMathUtility")
        inverse = self.get(self.get(self.sketch, "ModelToSketchTransform"), "Inverse")
        value = self.get(utility, "CreatePoint", self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_R8, point))
        return [float(number) for number in self.get(self.get(value, "MultiplyTransform", inverse), "ArrayData")]

    def build(self, case, session):
        self.model = self.rec.call("new native part", session.new_part)
        principal = BASE_NAMES[case["base"]]
        before = {name for _, name, kind in self.top_features() if kind == "RefPlane"}
        require(set(BASE_NAMES.values()) <= before, "native part template lacks the three expected principal supports")
        extension = self.get(self.model, "Extension")
        require(self.get(extension, "SelectByID2", principal, "PLANE", 0.0, 0.0, 0.0, False, 0, self.sw.nothing(), 0), "principal plane selection failed")
        flags = 8 | (256 if case["reverse"] else 0)
        created = self.get(self.get(self.model, "FeatureManager"), "InsertRefPlane", flags, case["distance_m"], 0, 0.0, 0, 0.0)
        require(created is not None, "InsertRefPlane returned no native reference plane")
        matches = [feature for feature, name, kind in self.top_features() if kind == "RefPlane" and name not in before]
        require(len(matches) == 1, "InsertRefPlane did not publish exactly one authored plane feature")
        plane, = matches
        self.set(plane, "Name", PLANE)
        self.get(self.model, "ClearSelection2", True)
        require(self.get(plane, "Select2", False, 0), "authored plane selection failed")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        self.sketch = self.get(manager, "ActiveSketch")
        require(self.sketch is not None, "the authored plane did not acquire a profile sketch")
        self.set(manager, "AddToDB", True)
        try:
            circle = self.get(manager, "CreateCircleByRadius", 0.0, 0.0, 0.0, case["radius_m"])
            require(circle is not None, "native circle profile creation failed")
        finally:
            self.set(manager, "AddToDB", False)
        self.segment_sources = {"entity-0": self.entity_binding(circle, "segment")}
        arc = self.typed(circle, "SketchArc")
        self.relation(17, [self.get(arc, "GetCenterPoint2")], ["entity-0.center"])
        radius = case["radius_m"]
        self.dimension(circle, "curve-0", radius, "radial", [radius * 1.7, radius * 1.3])
        self.get(manager, "InsertSketch", True)
        sketch = self.created_sketch_feature()
        self.set(sketch, "Name", SKETCH)
        self.get(self.model, "ClearSelection2", True)
        require(self.get(sketch, "Select2", False, 0), "plane-supported profile selection failed")
        args = (True, False, False, 0, 0, case["depth_m"], 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        boss = self.get(self.get(self.model, "FeatureManager"), "FeatureExtrusion3", *args)
        require(boss is not None, "plane-supported circle boss creation failed")
        self.set(boss, "Name", BOSS)
        require(self.get(self.model, "ForceRebuild3", False), "native source rebuild failed")

    def plane_dimension(self):
        from ReferencePlaneDimensions import dimension

        parameter, binding = dimension(self, PLANE, "distance")
        return parameter

    def edit_plane(self, value):
        dimension = self.plane_dimension()
        status = int(self.get(dimension, "SetSystemValue3", value, 1, self.sw.nothing()))
        require(status == 0, "plane distance dimension edit failed")
        self.rec.close_number("edited plane distance", self.get(dimension, "SystemValue"), value)
        require(self.get(self.model, "ForceRebuild3", False), "plane-supported boss did not rebuild after the plane edit")

    def snapshot(self, case, edited=False):
        from AuthorAssemblySources import feature_tree
        from ReferencePlaneDimensions import circle_geometry, dimension, feature

        wanted = geometry(case, edited)
        sketch_feature = feature(self, SKETCH)
        plane = feature(self, PLANE)
        boss = self.get(self.model, "FeatureByName", BOSS)
        require(all(value is not None for value in (sketch_feature, plane, boss)), "native source lost a required feature")
        self.sketch = self.get(sketch_feature, "GetSpecificFeature2")
        require(self.sketch is not None, "plane-supported profile has no native sketch")
        origin = self.world_point([0.0, 0.0, 0.0])
        end = self.world_point([0.0, 0.0, 1.0])
        normal = [end[index] - origin[index] for index in range(3)]
        for index in range(3):
            self.rec.close_number("independent support origin", origin[index], wanted["plane_origin"][index])
            self.rec.close_number("independent support normal", normal[index], wanted["normal"][index])
        extension = self.get(self.model, "Extension")
        require(int(self.get(extension, "GetWhatsWrongCount")) == int(self.get(extension, "NeedsRebuild2")) == 0, "source contains native rebuild warnings or errors")
        part = self.typed(self.model, "PartDoc")
        bodies = list(self.get(part, "GetBodies2", 0, True) or ())
        require(len(bodies) == 1, "plane-supported source must have exactly one visible solid")
        mass = self.rec.call("measure independent plane-supported cylinder", self.sw.mass, self.model)
        actual = [mass["volume"], mass["area"], *mass["com"]]
        expected = [wanted["volume"], wanted["area"], *wanted["com"]]
        require(all(math.isclose(value, target, rel_tol=5e-7, abs_tol=1e-12) for value, target in zip(actual, expected, strict=True)), "native body geometry differs from the authored plane and cylinder")
        definition = self.get(plane, "GetDefinition")
        require(definition is not None, "reference plane has no feature definition")
        definition = self.declared_interface(definition, "IRefPlaneFeatureData")
        require(self.get(definition, "AccessSelections", self.model, self.sw.nothing()), "reference-plane selections could not be accessed")
        try:
            constraint = int(self.indexed(definition, "Constraint", 0))
            reference = self.indexed(definition, "Reference", 0)
            distance = float(self.indexed(definition, "AngleOrDistance", 0))
            plane_types = {name: int(self.get(definition, name)) for name in ("Type", "Type2")}
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        require(constraint & 0xFF == 8 and reference is not None, "native source plane is not the requested referenced distance constraint")
        self.rec.close_number("feature-data offset distance", distance, wanted["distance_m"])
        parents = [{"name": str(self.get(value, "Name")), "type": str(self.get(value, "GetTypeName2"))} for value in self.get(plane, "GetParents") or ()]
        require({"name": BASE_NAMES[case["base"]], "type": "RefPlane"} in parents, "source plane does not retain its selected principal parent")
        plane_dimension, plane_binding = dimension(self, PLANE, "distance", wanted["distance_m"])
        plane_value = float(self.get(plane_dimension, "SystemValue"))
        self.rec.close_number("plane driving distance", plane_value, wanted["distance_m"])
        radius_dimension, radius_binding = dimension(self, SKETCH, "radius", wanted["radius_m"], "curve-0")
        radius_value = float(self.get(radius_dimension, "SystemValue"))
        self.rec.close_number("circle driving radius", radius_value, wanted["radius_m"])
        circle = circle_geometry(self, sketch_feature, wanted["radius_m"])
        depth_dimension = self.get(self.model, "Parameter", "D1@" + BOSS)
        require(depth_dimension is not None, "boss depth dimension is absent")
        depth = float(self.get(depth_dimension, "SystemValue"))
        self.rec.close_number("boss driving depth", depth, wanted["depth_m"])
        tree = feature_tree(self, self.model)
        require(all(row["error"] == 0 and row["warning"] is False and row["suppressed"] is False for row in tree), "native source feature tree contains a failed or suppressed feature")
        native_plane = self.declared_interface(self.get(plane, "GetSpecificFeature2"), "IRefPlane")
        transform = self.get(native_plane, "Transform")
        return {"body_count": 1, "mass_properties": mass, "expected_geometry": wanted, "feature_tree": tree,
                "plane": {"type": plane_types["Type"], "type2": plane_types["Type2"], "constraint": constraint,
                          "has_reference": True, "parents": parents, "distance_m": distance,
                          "transform": [float(value) for value in self.get(transform, "ArrayData")],
                          "dimension": {"name": str(self.get(plane_dimension, "FullName")), "value_m": plane_value}},
                "sketch_world_origin": origin, "sketch_world_normal": normal,
                "dimension_bindings": {"plane": plane_binding, "radius": radius_binding}, "circle_geometry": circle,
                "driving_dimensions_m": {"radius": radius_value, "plane_distance": plane_value, "boss_depth": depth},
                "update_stamp": int(self.get(self.model, "GetUpdateStamp"))}
