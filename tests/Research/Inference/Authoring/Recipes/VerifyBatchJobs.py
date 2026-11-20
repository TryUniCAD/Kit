# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from tests.Research.Inference.Authoring.Recipes.RecipeTargets import KRecipeTargets


# emitted batch jobs must isolate accepted artifact roles while legacy samples retain their original worker kind
def VerifyBatchJobs(Report: dict, PlanValue: dict) -> None:
    JobsById = {Entry["id"]: Entry for Entry in Report["definitions"]}
    Records = {Entry["name"]: Entry["record"] for Entry in Report["bindings"]}
    SeenSamples, SeenRoles = set(), set()
    for Submission in Report["submissions"]:
        assert len(Submission["samples"]) == len(Submission["capture"]) == 1
        Identity = Submission["samples"][0]
        assert Identity not in SeenSamples
        SeenSamples.add(Identity)
        Selection = PlanValue["samples"][Identity]["case"]
        Capture = JobsById[Submission["capture"][0]]
        Decoder = JobsById[Submission["decode"]]
        assert Decoder["depends_on"] == [Capture["id"]]
        Selector = Decoder["inputs"]["bundle"]
        assert Selector["dependency"] == Capture["id"]
        assert (Capture["id"], Selector["artifact"]) not in SeenRoles
        SeenRoles.add((Capture["id"], Selector["artifact"]))
        if Selection["recipe"] in KRecipeTargets:
            assert Capture["kind"] == "capture.catalogue.solidworks.batch"
            Bound = Records[Capture["inputs"]["cases"]]
            assert Bound["schema_version"] == 1 and 1 <= len(Bound["samples"]) <= 3
            assert Identity in {Entry["sample"] for Entry in Bound["samples"]}
            assert Selector["artifact"] in {"bundle.0", "bundle.1", "bundle.2"}
        else:
            assert Capture["kind"] == "capture.catalogue.solidworks"
            assert Selector["artifact"] == "bundle"
    assert SeenSamples == set(PlanValue["samples"])
