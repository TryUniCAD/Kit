from pathlib import Path

from AuthorCurves import digest
from ChamferModel import compare_six
from SelectedBodyMass import selected_body_mass
from SweepApi import options
from SweepModel import PATH, SECTION, SWEEP, require
from SweepSketches import SPEC, ZERO, SweepSketches

MARKED_SKETCHES = ((SECTION, 1), (PATH, 4))


class SweepAuthor(SweepSketches):
    def authored_density(self, value):
        key = self.constants["swMaterialPropertyDensity"]
        option = self.constants["swDetailingNoOptionSpecified"]
        require(self.get(self.extension, "SetUserPreferenceDouble", key, option, value),
                "native document rejected the explicitly authored mass density")
        self.inspect_density(value)

    def inspect_density(self, expected):
        value = float(self.get(self.extension, "GetUserPreferenceDouble", self.constants["swMaterialPropertyDensity"],
                               self.constants["swDetailingNoOptionSpecified"]))
        self.rec.close_number("actual document density in kg/m³", value, expected)
        return value

    def author(self, session, plan, density):
        template = Path(self.rec.call("locate installed part template", session.template, "part"))
        require(template.is_absolute() and template.is_file(), "native part template is unavailable")
        template_hash = digest(template)
        self.rec.data["part_template_sha256"] = template_hash
        self.model = self.rec.call("new ordinary native part", session.new_part)
        require(self.model is not None and digest(template) == template_hash, "unbound native template or new part")
        self.authored_density(density)
        with self.toggle(self.app, "swInputDimValOnCreate", False):
            for name, _ in MARKED_SKETCHES:
                self.create_sketch(name, plan)
        self.create_sweep(plan)

    def action_options(self, definition, *, write=False):
        expected = options(self.constants)
        if write:
            for name, value in expected.items():
                self.set(definition, name, value)
        else:
            expected["Direction"] = -1
        actual = {name: self.get(definition, name) for name in expected}
        self.rec.data["last_option_comparison"] = {"setting": write, "expected": expected, "actual": dict(actual)}
        self.rec.flush()
        require(actual == expected, "native sweep options differ from the explicit Standard one-direction boss")
        return actual

    def select_inputs(self, plan):
        self.get(self.model, "ClearSelection2", True)
        selection = self.get(self.model, "SelectionManager")
        for index, (name, mark) in enumerate(MARKED_SKETCHES):
            require(self.get(self.extension, "SelectByID2", name, "SKETCH", *ZERO, bool(index), mark,
                             self.sw.nothing(), 0), f"native {name} selection at mark {mark} failed")
        require(int(self.get(selection, "GetSelectedObjectCount2", -1)) == len(MARKED_SKETCHES),
                "native sweep selection contains unexpected items")
        rows = {}
        for name, mark in MARKED_SKETCHES:
            require(int(self.get(selection, "GetSelectedObjectCount2", mark)) == 1, f"invalid selection mark {mark}")
            kind = int(self.get(selection, "GetSelectedObjectType3", 1, mark))
            require(kind == self.constants["swSelSKETCHES"], f"mark {mark} is not an actual sketch")
            feature = self.get(selection, "GetSelectedObject6", 1, mark)
            selected = self.inspect_sketch(feature, name, plan)
            rows[name] = {"mark": mark, "select_type": kind, "geometry": selected}
        self.rec.data["marked_inputs"] = rows
        self.rec.flush()

    def create_sweep(self, plan):
        manager = self.get(self.model, "FeatureManager")
        definition = self.typed(self.get(manager, "CreateDefinition", self.constants["swFmSweep"]), "SweepFeatureData")
        self.action_options(definition, write=True)
        self.select_inputs(plan)
        feature = self.typed(self.get(manager, "CreateFeature", definition), "Feature")
        require(self.get(feature, "GetTypeName2") == "Sweep", "CreateFeature did not create an ordinary swept boss")
        self.set(feature, "Name", SWEEP)
        self.get(self.model, "ClearSelection2", True)

    def feature(self, name):
        return self.typed(self.get(self.model, "FeatureByName", name), "Feature")

    def parents(self, feature):
        expected = {name: "ProfileFeature" for name, _ in MARKED_SKETCHES}
        expected.update({row[0]: "RefPlane" for row in SPEC.values()})
        parents = [self.typed(parent, "Feature") for parent in self.get(feature, "GetParents") or ()]
        names = [str(self.get(parent, "Name")) for parent in parents]
        require(len(names) == len(expected) and set(names) == set(expected),
                "sweep did not retain both sketch owners and both supporting planes")
        for parent, name in zip(parents, names, strict=True):
            require(self.get(parent, "GetTypeName2") == expected[name] and self.same(parent, self.feature(name)),
                    f"actual sweep parent differs from the named {name} owner")
        return sorted(names)

    def definition(self, feature, plan, sketches):
        require(self.get(feature, "GetTypeName2") == "Sweep", "native feature is not Sweep")
        definition = self.typed(self.get(feature, "GetDefinition"), "SweepFeatureData")
        self.get(self.model, "ClearSelection2", True)
        require(self.get(definition, "AccessSelections", self.model, self.sw.nothing()),
                "native rollback cannot access actual sweep selections")
        try:
            facts = self.action_options(definition)
            facts.update(sweep_type=int(self.get(definition, "SweepType")),
                         is_boss=bool(self.get(definition, "IsBossFeature")),
                         is_thin=bool(self.get(definition, "IsThinFeature")),
                         guides=int(self.get(definition, "GetGuideCurvesCount")),
                         profile_type=int(self.get(definition, "GetProfileType")),
                         path_type=int(self.get(definition, "GetPathType")))
            self.rec.data["last_rollback_definition"] = facts
            self.rec.flush()
            require(facts["sweep_type"] == self.constants["swFmSweep"] and facts["is_boss"]
                    and not facts["is_thin"] and facts["guides"] == 0
                    and facts["profile_type"] == facts["path_type"] == self.constants["swSelSKETCHES"],
                    "native rollback is outside the two Standard-sketch boss inputs")
            for member, name in (("Profile", SECTION), ("Path", PATH)):
                actual = self.inspect_sketch(self.get(definition, member), name, plan)
                require(actual == sketches[name], f"rollback {member} does not select the same actual {name} segment")
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        self.get(self.model, "ClearSelection2", True)
        facts["parents"] = self.parents(feature)
        return facts

    def solid(self):
        solids = tuple(self.get(self.model, "GetBodies2", self.constants["swSolidBody"], False) or ())
        sheets = tuple(self.get(self.model, "GetBodies2", self.constants["swSheetBody"], False) or ())
        self.rec.data["last_body_count"] = {"solid": len(solids), "sheet": len(sheets)}
        self.rec.flush()
        require(len(solids) == 1 and not sheets, "native source must have one solid and no sheets")
        return self.typed(solids[0], "Body2")

    def measure_bounds(self, body, plan, label):
        bounds = []
        for side, sign in enumerate((-1.0, 1.0)):
            values = []
            for axis in range(3):
                direction = [sign if index == axis else 0.0 for index in range(3)]
                outputs = [self.sw.VARIANT(self.sw.pythoncom.VT_BYREF | self.sw.pythoncom.VT_R8, 0.0) for _ in range(3)]
                require(self.get(body, "GetExtremePoint", *direction, *outputs), "native Cartesian extreme is unavailable")
                values.append(float(outputs[axis].value))
            self.vector_check(f"{label} bound {side}", values, plan["bounds"][side])
            bounds.append(values)
        return bounds

    def close_six(self, label, actual, expected, near_zero):
        error, tolerance, passed = compare_six(actual, expected, near_zero)
        self.rec.data["checks"].append({"name": label, "actual": actual, "expected": expected, "passed": passed,
                                        "absolute_error": error, "absolute_tolerance": tolerance,
                                        "method": "half_unit_at_sixth_significant_place_or_near_zero"})
        self.rec.flush()
        require(passed, f"{label} differs from the independent analytic prediction")

    def body_topology(self, body, plan, label):
        faces = list(self.get(body, "GetFaces") or ())
        edges = list(self.get(body, "GetEdges") or ())
        vertices = list(self.get(body, "GetVertices") or ())
        require(2 < len(faces) <= 16 and 2 <= len(edges) <= 32 and len(vertices) <= 32,
                "unexpected quarter-tube topology")
        rows = []
        for face in faces:
            surface = self.get(face, "GetSurface")
            producer = self.get(face, "GetFeature")
            row = {"type": "plane" if self.get(surface, "IsPlane") else "curved",
                   "torus": bool(self.get(surface, "IsTorus")), "area_m2": float(self.get(face, "GetArea")),
                   "producer": str(self.get(producer, "Name")), "producer_type": str(self.get(producer, "GetTypeName2"))}
            rows.append(row)
            self.rec.data["last_body_faces"] = rows
            self.rec.flush()
            require(row["producer"] == SWEEP and row["producer_type"] == "Sweep", "body face has another feature owner")
        caps = [row for row in rows if row["type"] == "plane"]
        require(len(caps) == 2, "the Standard quarter-tube does not have two native caps")
        for row in caps:
            self.close_six(f"{label} cap area", row["area_m2"], plan["cap_area"], 1e-16)
        self.close_six(f"{label} total curved area", sum(row["area_m2"] for row in rows if row["type"] == "curved"),
                       plan["area"] - 2 * plan["cap_area"], 1e-16)
        return {"faces": len(faces), "edges": len(edges), "vertices": len(vertices), "face_rows": rows}

    def measure_body(self, plan, label):
        body = self.solid()
        topology = self.body_topology(body, plan, label)
        legacy = self.rec.call("legacy native SI mass properties", self.sw.mass, self.model)
        self.rec.data["last_legacy_mass_measurement"] = legacy
        measured = selected_body_mass(self, body)
        for key, epsilon in (("volume", 1e-21), ("area", 1e-16), ("mass", 1e-17)):
            self.close_six(f"{label} {key}", measured[key], plan[key], epsilon)
        require(len(measured["com"]) == 3, "native centre of mass does not have three coordinates")
        for axis, (a, b) in enumerate(zip(measured["com"], plan["com"], strict=True)):
            self.close_six(f"{label} COM xyz[{axis}]", a, b, 1e-10)
        return {"native": measured, "legacy_observation": legacy,
                "topology": topology, "bounds_m": self.measure_bounds(body, plan, label)}

    def diagnostics(self):
        return int(self.get(self.extension, "GetWhatsWrongCount"))

    def snapshot(self, plan, density, label):
        require(self.get(self.model, "ForceRebuild3", False) and self.diagnostics() == 0, "native rebuild failed or warned")
        config_names = list(self.get(self.model, "GetConfigurationNames") or ())
        active = self.get(self.get(self.model, "ConfigurationManager"), "ActiveConfiguration")
        require(config_names == [str(self.get(active, "Name"))], "expected one active authored configuration")
        tree = self.feature_tree(required_names=(SECTION, PATH, SWEEP))
        self.rec.data[label] = result = {"tree": tree, "configuration": config_names[0]}
        self.rec.flush()
        result["density_kg_m3"] = self.inspect_density(density)
        sketches = {name: self.inspect_sketch(self.feature(name), name, plan) for name, _ in MARKED_SKETCHES}
        result["sketches"] = sketches
        result["drivers"] = {name: self.driving_dimension(self.feature(name), name, plan)[0] for name, _ in MARKED_SKETCHES}
        result["definition"] = self.definition(self.feature(SWEEP), plan, sketches)
        require(self.diagnostics() == 0, "restoring native rollback introduced diagnostics")
        result["body"] = self.measure_body(plan, label)
        self.rec.flush()
        return result

    def edit(self, role, original, edited):
        name = {"section": SECTION, "path": PATH}[role]
        prior, dimension = self.driving_dimension(self.feature(name), name, original)
        target = edited[SPEC[name][2]]
        self.set_driver(dimension, target)
        self.rec.data["edit"] = {"source": prior, "requested_m": target, "role": role, "success": True}
        self.rec.flush()
