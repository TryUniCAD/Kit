from AuthorObliqueCylinder import ObliqueAuthor
from ObliqueFlipPlan import NAMES, angle_plan, boss_arguments, hinge


class ObliqueFlipAuthor(ObliqueAuthor):
    def plane_arguments(self, key, value):
        return angle_plan(key, value)["arguments"]

    def extrusion_arguments(self, case):
        return boss_arguments(case)

    def create_axis(self, name, parents):
        feature = super().create_axis(name, parents)
        for key in ("hinge_a", "hinge_b"):
            if name == NAMES[key]:
                self.directed_line(key, self.axis_geometry(feature), hinge(key))
        return feature

    def directed_line(self, label, observed, expected):
        for index in range(3):
            self.rec.close_number(
                label + " actual directed axis component",
                observed["unit"][index],
                expected[index],
            )

    def snapshot(self, case, steps=0):
        result = super().snapshot(case, steps)
        wanted = self.predictions[str(steps)]
        for key in ("hinge_a", "hinge_b"):
            self.directed_line(key, result["axes"][key], wanted["hinge_units"][key])
        self.directed_line(
            "selected direction",
            result["axes"]["direction"],
            wanted["directed_axis_unit"],
        )
        self.directed_line(
            "actual extrusion direction owner",
            result["extrusion"]["direction_reference"]["axis"],
            wanted["directed_axis_unit"],
        )
        for key in ("angle_a", "angle_b"):
            for index in range(3):
                self.rec.close_number(
                    key + " signed plane normal",
                    result["planes"][key]["normal"][index],
                    wanted["angle_plane_normals"][key][index],
                )
            self.rec.data.setdefault("flip_observations", []).append(
                {
                    "owner": NAMES[key],
                    "planned_reverse": wanted["angle_input_plans"][key]["reverse"],
                    "indexed_constraint": result["planes"][key]["constraints"][0],
                }
            )
        self.rec.flush()
        return result
