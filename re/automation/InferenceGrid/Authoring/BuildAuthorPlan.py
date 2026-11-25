# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.SolidWorks.SolidBatchSize import KSolidBatchCases
from InferenceGrid.Authoring.ReadCases import KRecipeModes, MakeCase, ReadOverrides
from InferenceGrid.Authoring.RecipeGrid import ExpandCaseGrid
from Records import digest


# aliases share authored samples while distinct parameter choices retain independent native evidence
def BuildAuthorPlan(
    Catalogues, Revision, CasePath=None, ModeValue="discovery", GridValue="baseline"
):
    if ModeValue not in KRecipeModes:
        raise ValueError("unknown catalogue capture mode")
    Selected = ReadOverrides(CasePath, Catalogues, ModeValue)
    if Selected is None:
        Selected = []
        for Application, Catalogue in sorted(Catalogues.items()):
            for FeatureKey in sorted(Catalogue["features"]):
                CaseValue = MakeCase(Application, FeatureKey, {}, ModeValue)
                if CaseValue is not None:
                    Selected.append(CaseValue)
    Selected = ExpandCaseGrid(Selected, ModeValue, GridValue)
    Samples, Features = {}, {}
    for Application, Catalogue in sorted(Catalogues.items()):
        Features[Application] = {
            FeatureKey: {
                "status": "not_selected" if CasePath else "authoring_recipe_unavailable"
            }
            for FeatureKey in sorted(Catalogue["features"])
        }
    for Selection in Selected:
        Application = Selection["application"]
        CaseValue = Selection["case"]
        Identity = Application + ":" + CaseValue["id"]
        Existing = Samples.setdefault(Identity, Selection)
        if Existing["case"] != CaseValue:
            raise ValueError("catalogue authoring case identities collide")
        Entry = Features[Application][Selection["feature"]]
        if Entry["status"] != "planned":
            Entry.update(status="planned", samples=[])
        if Identity not in Entry["samples"]:
            Entry["samples"].append(Identity)
    if not Samples:
        raise ValueError(
            "selected catalogue has no executable cases for this capture mode"
        )
    ResultValue = {
        "schema_version": 1,
        "source_revision": Revision,
        "mode": ModeValue,
        "catalogues": {
            Application: Catalogue["catalogue_sha256"]
            for Application, Catalogue in sorted(Catalogues.items())
        },
        "features": Features,
        "samples": dict(sorted(Samples.items())),
        "inputs_sha256": digest([Revision, ModeValue, Selected]),
    }
    if GridValue != "baseline":
        ResultValue["parameter_grid"] = GridValue
    if "solidworks" in Catalogues:
        ResultValue["solidworks_batch_version"] = 1
        ResultValue["solidworks_batch_size"] = KSolidBatchCases
    return ResultValue
