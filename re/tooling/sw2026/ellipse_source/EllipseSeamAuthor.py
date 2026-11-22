from pathlib import Path

from AuthorCurves import digest
from EllipseAuthor import BOSS, FRONT, SKETCH, EllipseAuthor
from EllipseModel import require
from EllipsePacket import predictions_equal
from EllipseSeamObserve import observe
from EllipseSeamPacket import TEMPLATE_SHA256


class SeamAuthor(EllipseAuthor):
    def draw_profile(self, session, plan, api):
        template = Path(self.rec.call("default native part template", session.template, "part"))
        require(template.is_absolute() and template.is_file(), "missing actual blank-part template")
        self.rec.data["template_sha256"] = digest(template)
        require(self.rec.data["template_sha256"] == TEMPLATE_SHA256, "ellipse template differs from the disclosed control")
        self.model = self.rec.call("new blank native part", session.new_part)
        require(digest(template) == self.rec.data["template_sha256"], "native part template changed")
        plane = self.get(self.model, "FeatureByName", FRONT)
        require(self.get(plane, "GetTypeName2") == "RefPlane" and self.get(plane, "Select2", False, 0),
                "canonical Front datum could not be selected")
        self.selected(plane)
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        sketch = self.get(manager, "ActiveSketch")
        require(sketch is not None, "ellipse needs an actual active sketch")
        old = bool(self.get(manager, "AddToDB"))
        self.set(manager, "AddToDB", True)
        try:
            coords = [value for point in plan["points_m"] for value in point]
            drawn = self.get(manager, "CreateEllipse", *coords)
            require(drawn is not None, "native CreateEllipse returned no sketch member")
            observe(self, "draw_open", sketch, self.segment(sketch, plan, drawn), api)
        finally:
            self.set(manager, "AddToDB", old)
        self.get(manager, "InsertSketch", True)
        require(self.get(manager, "ActiveSketch") is None, "native profile remained open after sketch close")
        feature = self.created_sketch_feature()
        self.set(feature, "Name", SKETCH)
        closed = self.get(feature, "GetSpecificFeature2")
        observe(self, "sketch_closed", closed, self.profile(closed, plan), api)
        return feature

    def create_boss(self, feature, plan, api):
        self.get(self.model, "ClearSelection2", True)
        require(self.get(feature, "Select2", False, 0), "ordinary ellipse profile cannot be selected for boss")
        self.selected(feature)
        blind, depth = self.constants["swEndCondBlind"], plan["states"][0]["depth_m"]
        args = (True, False, False, blind, blind, depth, 0.0, False, False, False, False, 0.0, 0.0,
                False, False, False, False, True, True, True, 0, 0.0, False)
        boss = self.get(self.get(self.model, "FeatureManager"), "FeatureExtrusion3", *args)
        require(boss is not None, "native FeatureExtrusion3 did not make the ellipse boss")
        self.set(boss, "Name", BOSS)
        self.get(self.model, "ClearSelection2", True)
        self.profile_stage("boss_created", plan, api)

    def profile_stage(self, stage, plan, api):
        sketch = self.get(self.model, "FeatureByName", SKETCH)
        require(self.get(sketch, "GetTypeName2") == "ProfileFeature", "native ellipse profile role changed")
        profile = self.get(sketch, "GetSpecificFeature2")
        return observe(self, stage, profile, self.profile(profile, plan), api)

    def check_shape(self, role, stage, plan, api):
        if role == "boss":
            self.snapshot("shape", plan)
            observed = self.profile_stage(stage, plan, api)
            require(predictions_equal(observed["ellipse"], self.rec.data["shape"]["profile"]),
                    "native mass lifecycle did not retain the actual measured ellipse")
            return
        self.clean_rebuild()
        for kind in ("swSolidBody", "swSheetBody"):
            require(not self.get(self.model, "GetBodies2", self.constants[kind], False),
                    "sketch-only source unexpectedly has a solid or sheet")
        configs = list(self.get(self.model, "GetConfigurationNames") or ())
        active = self.get(self.get(self.model, "ConfigurationManager"), "ActiveConfiguration")
        require(configs == [str(self.get(active, "Name"))] and self.get(self.model, "FeatureByName", BOSS) is None,
                "sketch-only profile has an alternate native document scope")
        tree = self.feature_tree(required_names=(SKETCH,))
        profile_rows = [row["name"] for row in tree if row["type"] == "ProfileFeature"]
        require(profile_rows == [SKETCH] and not any(row["type"] == "Extrusion" for row in tree),
                "sketch-only native tree differs from its single ordinary profile")
        profile = self.profile_stage(stage, plan, api)["ellipse"]
        self.rec.data["shape"] = {"profile": profile, "configurations": configs, "tree": tree,
                                  "body": {"solid_count": 0, "sheet_count": 0}}
        self.rec.flush()
