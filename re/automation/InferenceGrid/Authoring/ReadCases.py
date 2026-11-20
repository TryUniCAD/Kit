# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.FeatureSpecs import SpecFor
from Records import digest, read_record

# reserved recipe families must never enter discovery through an alias
KRecipeModes = {
    "discovery": {"P01", "P03", "P04"},
    "qualification": {"P02"},
    "holdout": {"P05"},
}


# native generators receive only identities and parameters validated for their application
def NormalizeCase(Application, CaseValue):
    if Application == "fusion":
        from CaptureTools.Catalogue.Fusion.FusionParams import ValidateFusion

        return ValidateFusion(CaseValue)
    if Application == "solidworks":
        from CaptureTools.Catalogue.SolidWorks.ValidateSolid import ValidateSolid

        return ValidateSolid(CaseValue)
    raise ValueError("authoring requires a Fusion or SOLIDWORKS catalogue")


# an explicit override file selects cases without interpreting written instructions as code
def ReadOverrides(CasePath, Catalogues, ModeValue):
    if CasePath is None:
        return None
    RecordValue = read_record(CasePath)
    if (
        set(RecordValue) != {"schema_version", "cases"}
        or type(RecordValue["schema_version"]) is not int
        or RecordValue["schema_version"] != 1
    ):
        raise ValueError("authoring cases require schema_version one and cases")
    CasesValue = RecordValue["cases"]
    if not isinstance(CasesValue, list) or not 1 <= len(CasesValue) <= 128:
        raise ValueError("authoring requires one to 128 explicit cases")
    Selected = []
    for CaseValue in CasesValue:
        if (
            not isinstance(CaseValue, dict)
            or not {"application", "feature"} <= set(CaseValue)
            or set(CaseValue) - {"application", "feature", "parameters", "options"}
        ):
            raise ValueError("invalid catalogue authoring case fields")
        Application = CaseValue["application"]
        FeatureKey = CaseValue["feature"]
        if (
            Application not in Catalogues
            or FeatureKey not in Catalogues[Application]["features"]
        ):
            raise ValueError("authoring case is outside the selected catalogue")
        Selected.append(
            MakeCase(Application, FeatureKey, CaseValue, ModeValue, Required=True)
        )
    return Selected


# executable paired builders remain distinct from broader plain language recipe specifications
def MakeCase(Application, FeatureKey, Overrides, ModeValue, *, Required=False):
    Written = SpecFor(FeatureKey)
    RecipeKey = None if Written is None else Written.get("pair_recipe")
    if RecipeKey not in KRecipeModes[ModeValue]:
        if Required:
            raise ValueError(
                "feature has no executable authoring recipe in the selected capture mode"
            )
        return None
    CaseValue = NormalizeCase(
        Application,
        {
            "recipe": RecipeKey,
            "parameters": Overrides.get("parameters", {}),
            "options": Overrides.get("options", {}),
        },
    )
    return {
        "application": Application,
        "feature": FeatureKey,
        "case": {"id": digest(CaseValue)[:16], **CaseValue},
    }
