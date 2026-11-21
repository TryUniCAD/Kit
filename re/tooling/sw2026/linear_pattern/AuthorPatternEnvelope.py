from math import dist, isfinite

import Swapp
from AuthorCurves import require
from AuthorObliqueCylinder import ObliqueAuthor
from LinearPatternAuthor import LinearPatternAuthor, PATTERN, PLATE, PLATE_SKETCH, ROLES, SEED, SEED_SKETCH
from LinearPatternSpecs import rectangle


class PatternEnvelopeAuthor(LinearPatternAuthor):
    def __init__(self, application, recorder, api, spec):
        super().__init__(application, recorder, Swapp)
        self.spec = spec
        self.datum_author = ObliqueAuthor(application, recorder, Swapp, api, None)
        plate_min, plate_max = spec["plate_box_m"]
        seed_min, seed_max = spec["seed_box_m"]
        self.case = {
            "axis_plane": spec["direction_datum"]["name"],
            "plate_origin_m": plate_min[:2],
            "plate_size_m": [b - a for a, b in zip(plate_min[:2], plate_max[:2], strict=True)],
            "plate_depth_m": plate_max[2],
            "seed_offset_m": [a - b for a, b in zip(seed_min[:2], plate_min[:2], strict=True)],
            "seed_size_m": [b - a for a, b in zip(seed_min[:2], seed_max[:2], strict=True)],
            "seed_extra_depth_m": seed_max[2] - plate_max[2],
            "spacing_m": spec["arms"][0]["spacing_m"],
            "instances": spec["arms"][0]["count"],
        }
        if len(spec["arms"]) > 1:
            self.case["edit_spacing_m"] = spec["arms"][1]["spacing_m"]

    def connect(self, model):
        self.model = self.datum_author.model = model

    def observe_hinge(self, axis):
        hinge = self.spec["hinge"]
        result = self.datum_author.axis_geometry(axis)
        self.datum_author.check_line("through origin hinge", result, hinge["axis_model"])
        require(dist(result["unit"], hinge["axis_model"]) <= 1e-10,
                "actual hinge direction differs from the frozen source recipe")
        parents = self.datum_author.parents(axis)
        require(len(parents) == len(hinge["selection"])
                and {row["name"] for row in parents} == {row["name"] for row in hinge["selection"]},
                "actual hinge no longer joins both selected datum planes")
        return {**result, "parents": parents}

    def create_datum(self):
        hinge = self.spec["hinge"]
        direction = self.spec["direction_datum"]
        axis = self.datum_author.create_axis(hinge["name"], [row["name"] for row in hinge["selection"]])
        self.observe_hinge(axis)
        self.datum_author.create_plane(
            direction["name"], [(row["name"], row["mark"]) for row in direction["selection"]],
            direction["arguments"],
        )
        self.observe_datum()

    def observe_datum(self):
        feature, plane = self.direction_plane(self.case)
        direction = self.spec["direction_datum"]
        wanted = direction["required_signed_normal"]
        result = self.datum_author.plane_geometry(feature)
        hinge = self.observe_hinge(self.datum_author.feature(self.spec["hinge"]["name"]))
        self.rec.data["latest_datum_frame"] = {"plane": result, "hinge": hinge}
        self.rec.flush()
        origin, normal = result["origin_m"], result["normal"]
        opposite = [-value for value in wanted]
        require(len(origin) == len(normal) == 3 and all(isfinite(value) for value in (*origin, *normal))
                and dist(origin, direction["origin_m"]) <= 1e-10,
                "oblique pattern requires the actual through-origin datum")
        reverse = dist(normal, opposite) <= 1e-10
        require(reverse or dist(normal, wanted) <= 1e-10,
                "authored oblique datum normal is outside its prospectively frozen two signs")
        actual_parents = {row["name"] for row in self.datum_author.parents(feature)}
        require(actual_parents == {row["name"] for row in direction["selection"]},
                "actual oblique plane has different input owners")
        definition = self.datum_author.declared_interface(
            self.get(feature, "GetDefinition"), "IRefPlaneFeatureData"
        )
        require(self.get(definition, "AccessSelections", self.model, Swapp.nothing()),
                "oblique plane selection owners are inaccessible")
        constraints = []
        try:
            for index, expected in enumerate(direction["selection"]):
                selector = self.datum_author.indexed(definition, "Reference", index)
                target = self.datum_author.feature(expected["name"])
                specific = self.get(target, "GetSpecificFeature2")
                captured = self.persistent(selector, "actual plane input")
                identities = [self.persistent(target, "expected plane input")["hex"]]
                if specific is not None:
                    identities.append(self.persistent(specific, "expected geometry input")["hex"])
                require(captured["hex"] in identities, "oblique plane input is a different actual object")
                flags = int(self.datum_author.indexed(definition, "Constraint", index))
                angle = float(self.datum_author.indexed(definition, "AngleOrDistance", index))
                expected_flags, wanted_angle = direction["arguments"][2 * index:2 * index + 2]
                require(flags & 0xFF == expected_flags, "oblique plane constraint mode changed")
                self.rec.close_number("oblique plane angle " + str(index), abs(angle), wanted_angle)
                constraints.append({"flags": flags, "angle_or_distance": angle, "input": captured})
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        self.case["reverse"] = reverse
        return {**result, "hinge": hinge, "signed_normal": [-value for value in normal] if reverse else normal,
                "reverse": reverse, "constraints": constraints, "feature_reference": self.persistent(feature, "direction owner"),
                "geometry_reference": self.persistent(plane, "direction geometry")}

    def create_pattern(self, seed):
        self.select_pattern_inputs(self.case, seed)
        manager = self.get(self.model, "FeatureManager")
        definition = self.typed(self.get(manager, "CreateDefinition", 6), "LinearPatternFeatureData")
        for name in ("BodyPattern", "GeometryPattern", "VarySketch", "InstancesToVary"):
            self.set(definition, name, False)
        for name, value in (
            ("D1EndCondition", 0), ("D1Spacing", self.case["spacing_m"]),
            ("D1TotalInstances", self.case["instances"]), ("D1ReverseDirection", self.case["reverse"]),
        ):
            self.set(definition, name, value)
        require(not self.get(definition, "IsDirection2Specified") and self.get(definition, "D2Axis") is None
                and not (self.get(definition, "SkippedItemArray") or ()), "fresh pattern has alternate direction or skips")
        feature = self.get(manager, "CreateFeature", definition)
        require(feature is not None, "ordinary native oblique pattern creation returned null")
        self.set(feature, "Name", PATTERN)
        self.get(self.model, "ClearSelection2", True)

    def observe_geometry(self, label, expected):
        require(self.get(self.model, "ForceRebuild3", False), "native pattern rebuild failed")
        extension = self.get(self.model, "Extension")
        require(int(self.get(extension, "GetWhatsWrongCount")) == 0, "native pattern has rebuild errors or warnings")
        features = Swapp.features(self.model)
        require(features and all(row.get("error") == 0 and row.get("warning") is False and not row.get("error_query_error")
                                 for row in features), "native feature errors or warnings")
        require(self.rec.call("solid body count", Swapp.bodies, self.model) == 1, "expected one joined solid")
        mass = self.rec.call("actual solid properties", Swapp.mass, self.model)
        require(mass and not mass.get("error") and isfinite(mass["mass"]) and mass["mass"] > 0,
                "native solid has no measurable mass")
        bounds = self.extreme_bounds()
        self.rec.close_number(label + " volume", mass["volume"], expected["volume_m3"], absolute=1e-22)
        self.rec.close_number(label + " area", mass["area"], expected["area_m2"], absolute=1e-18)
        for index, (actual, target) in enumerate(zip(mass["com"], expected["centroid_m"], strict=True)):
            self.rec.close_number(label + " center of mass " + str(index), actual, target, absolute=1e-10)
        for index, (actual, target) in enumerate(zip(bounds["minmax"], expected["bounds_m"], strict=True)):
            self.rec.close_number(label + " exact extent " + str(index), actual, target, absolute=1e-9)
        return {"mass": mass, "bounds": bounds, "expected": expected, "bodies": 1}

    def build_envelope(self, session):
        self.connect(self.rec.call("new independent pattern source", session.new_part))
        self.make_boss(self.case, False)
        seed = self.make_boss(self.case, True)
        self.create_datum()
        self.rec.data["pre_pattern"] = self.observe_geometry("prior joined solid", self.spec["expected_before_pattern"])
        self.rec.flush()
        self.create_pattern(seed)

    def envelope_state(self, label, arm_index):
        arm = self.spec["arms"][arm_index]
        result = self.observe_geometry(label, arm["expected_final"])
        datum = self.observe_datum()
        tree = self.feature_tree(required_names=(*ROLES, self.spec["hinge"]["name"], self.case["axis_plane"]))
        features = [row["name"] for row in tree if not row["suppressed"]]
        require(features.index(PLATE) < features.index(SEED) < features.index(PATTERN)
                and features.index(self.spec["hinge"]["name"]) < features.index(self.case["axis_plane"]) < features.index(PATTERN),
                "native ordered feature inputs changed")
        plate, _ = self.inspect_profile(PLATE_SKETCH, rectangle(self.case, False))
        seed, _ = self.inspect_profile(SEED_SKETCH, rectangle(self.case, True))
        identity = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        for profile in (plate, seed):
            require(len(profile["model_to_sketch"]) == len(identity) and dist(profile["model_to_sketch"], identity) <= 1e-10,
                    "independent box prediction requires the actual Front frame")
        pattern = self.inspect_pattern(self.case, arm["spacing_m"], arm["count"])
        require(len(pattern["parents"]) == 2 and set(pattern["parents"]) == {SEED, self.case["axis_plane"]}
                and pattern["feature_scope_body_count"] == 1
                and pattern["values"]["FeatureScope"] is True
                and pattern["values"]["AutoSelect"] is False
                and pattern["values"]["D2Spacing"] == 0 and pattern["values"]["D2TotalInstances"] == 1,
                "the oblique sample left the actual one-seed, one-direction, one-stock profile")
        require(pattern["plane_feature_reference"]["hex"] == datum["feature_reference"]["hex"]
                and pattern["axis_reference"]["hex"] == datum["geometry_reference"]["hex"],
                "native pattern lost the measured oblique datum")
        require(pattern["dimensions"]["bindings"]["spacing"].split("@")[:2] == ["D3", PATTERN]
                and pattern["dimensions"]["bindings"]["instances"].split("@")[:2] == ["D1", PATTERN],
                "actual spacing and count owners differ")
        result.update(datum=datum, pattern=pattern, tree=tree, plate_profile=plate, seed_profile=seed,
                      plate_boss=self.inspect_feature(PLATE, PLATE_SKETCH, self.case["plate_depth_m"] * 1000, True),
                      seed_boss=self.inspect_feature(SEED, SEED_SKETCH, self.spec["seed_box_m"][1][2] * 1000, True))
        self.rec.data[label] = result
        self.rec.flush()
        return result
