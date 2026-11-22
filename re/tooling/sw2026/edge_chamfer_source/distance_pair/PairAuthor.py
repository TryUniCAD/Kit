from math import isclose

import Swapp
from ChamferAuthor import BOSS, ChamferAuthor
from ChamferModel import predict_legs
from FilletModel import require


def pair_values(case, edited):
    first, second = [value * 0.001 for value in case["distances_mm"]]
    if not edited:
        return first, second
    modified = case["edit_mm"] * 0.001
    return (modified, modified) if case["equal"] else (first, modified)


def pair_plan(case):
    states = {}
    for name, edited in (("initial", False), ("edited", True)):
        pair = pair_values(case, edited)
        choices = (pair,) if case["equal"] else (pair, pair[::-1])
        states[name] = [
            {"branch": [hand], "geometry": predict_legs(case, distances)}
            for hand, distances in enumerate(choices)
        ]
    return {"stock": predict_legs(case), "states": states}


class PairAuthor(ChamferAuthor):
    feature_name = "DistancePairEdgeChamfer"

    def profile_params(self, case, edited):
        return pair_values(case, edited)

    def author(self, case, session, stock):
        manager, edge, proof = self.author_stock(case, session, stock)
        self.select_chamfer(edge, proof)
        first, second = self.profile_params(case, False)
        mode = self.constants["swChamferDistanceDistance"]
        if case["equal"]:
            mode |= self.constants["swChamferEqualDistance"]
            args = (0.0, 0.0, first, 0.0, 0.0, 0.0)
        else:
            args = (0.0, 0.0, 0.0, first, second, 0.0)
        self.rec.data["insertion"] = {"mode": mode, "arguments": args}
        self.rec.flush()
        feature = self.get(manager, "InsertFeatureChamfer", 0, mode, *args)
        require(feature is not None, "native distance chamfer returned no feature")
        self.set(feature, "Name", self.feature_name)
        self.get(self.model, "ClearSelection2", True)

    def definition(self, feature, boss, endpoints, params):
        kind = str(self.get(feature, "GetTypeName2"))
        require(kind == "Chamfer", f"native feature type was {kind}")
        data = self.typed(self.get(feature, "GetDefinition"), "ChamferFeatureData2")
        require(bool(self.get(data, "AccessSelections", self.model, Swapp.nothing())),
                "could not roll back the native distance chamfer")
        try:
            fields = {
                key: self.get(data, key)
                for key in ("Type", "EqualDistance", "TangentPropagation", "KeepFeatures",
                            "PropagateFeatureToParts", "GetEdgeCount", "GetFaceCount", "LoopCount")
            }
            distances = tuple(float(self.get(data, "GetEdgeChamferDistance", index)) for index in (0, 1))
            edges = tuple(self.get(data, "Edges") or ())
            fields["distance_by_side_m"] = distances
            fields["alternate_inputs"] = {"faces": len(self.get(data, "Faces") or ()),
                                          "loops": len(self.get(data, "Loops") or ())}
            self.rec.data["last_native_definition"] = fields
            self.rec.flush()
            equal = params[0] == params[1]
            require(fields["Type"] == self.constants["swChamferDistanceDistance"]
                    and bool(fields["EqualDistance"]) == equal, "native mode or equality differs")
            require(not any(fields[name] for name in
                            ("TangentPropagation", "KeepFeatures", "PropagateFeatureToParts"))
                    and not any(fields["alternate_inputs"].values()) and fields["GetEdgeCount"] == len(edges) == 1,
                    "native distance chamfer unexpectedly has additional options or owners")
            found, proof = self.find_edge(endpoints, boss)
            selected = self.typed(edges[0], "Edge")
            require(self.same(found, selected), "rolled-back chamfer references a different stock edge")
            fields["GetIsFlipped"] = self.get(data, "GetIsFlipped", self.typed(selected, "Entity"))
            self.rec.close_number("native first distance owner", distances[0], params[0])
            if not equal:
                self.rec.close_number("native second distance owner", distances[1], params[1])
        finally:
            self.get(data, "ReleaseSelectionAccess")
        parents = tuple(self.get(feature, "GetParents") or ())
        require(any(self.same(parent, boss) for parent in parents), "distance chamfer lost its stock parent")
        return {"type": kind, "fields": fields, "edge": proof, "feature_reference": self.reference(feature),
                "parents": [str(self.get(parent, "Name")) for parent in parents]}

    def display_drivers(self, feature, params):
        inventory, live = self.driver_inventory(feature)
        roles = ("shared",) if params[0] == params[1] else ("first", "second")
        require(len(live) == len(roles), "independent native distance driver count differs")
        bindings = {}
        for role, value in zip(roles, params):
            matches = [entry for entry in live.values()
                       if isclose(entry[0]["value_si"], value, rel_tol=0.0, abs_tol=1e-10)]
            require(len(matches) == 1, f"native distance driver for {role} is missing or ambiguous")
            bindings[role] = matches[0]
        return inventory, bindings

    def edit(self, case):
        feature = self.get(self.model, "FeatureByName", self.feature_name)
        _, bindings = self.display_drivers(feature, self.profile_params(case, False))
        role = "shared" if case["equal"] else "second"
        row, dimension = bindings[role]
        target = self.profile_params(case, True)[1]
        status = int(self.get(dimension, "SetSystemValue3", target, self.constants["swSetValue_InThisConfiguration"],
                              Swapp.nothing()))
        self.rec.data["edit"] = {"role": role, "driver": row, "target_si": target, "status": status}
        self.rec.flush()
        require(status == self.constants["swSetValue_Successful"], f"native distance driver edit returned {status}")
        self.rec.close_number("native distance after edit", self.get(dimension, "SystemValue"), target)
