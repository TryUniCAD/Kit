# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose

from CaptureTools.Catalogue.Recipes.ExpectedRecipe import ExpectedRecipe
from CaptureTools.Catalogue.SolidWorks.CheckProgramOps import CheckProgramOps
from CaptureTools.Catalogue.SolidWorks.CheckProfile import CheckProfile


# written recipes require measured native semantics beyond coincident solid geometry
def CheckProgramShape(CaseValue, Observed):
    Expected = ExpectedRecipe(CaseValue)
    Program = CaseValue["options"]["program"]
    Bounds = Expected["bounds_mm"]
    ExpectedBounds = Bounds[0] + Bounds[1]
    if (
        Observed["body_count"] != Expected["body_count"]
        or Observed["surface_body_count"] != 0
        or not isclose(
            Observed["volume_mm3"], Expected["volume_mm3"], rel_tol=1e-9, abs_tol=1e-6
        )
        or len(Observed["center_of_mass_mm"]) != 3
        or len(Observed["bounds_mm"]) != 6
        or any(
            not isclose(Actual, Target, rel_tol=1e-9, abs_tol=1e-6)
            for Actual, Target in zip(
                Observed["center_of_mass_mm"] + Observed["bounds_mm"],
                Expected["center_of_mass_mm"] + ExpectedBounds,
                strict=True,
            )
        )
    ):
        raise ValueError("SOLIDWORKS written recipe body measurements differ")
    Features = Observed["feature_tree"]
    if not Features or any(
        Feature["suppressed"] is not False
        or Feature["error_code"] != 0
        or Feature["warning"] is not False
        for Feature in Features
    ):
        raise ValueError("SOLIDWORKS written recipe has an unhealthy native feature")
    Names = [Feature["name"] for Feature in Features]
    Required = {"Origin", "RecipeProfile", "RecipeFeature"}
    if Program["seed"] is not None:
        Required |= {"SeedProfile", "SeedFeature"}
    if Program["operation"]["end"]["kind"] == "up_to_plane":
        Required.add("EndPlane")
    if len(Names) != len(set(Names)) or not Required <= set(Names):
        raise ValueError("SOLIDWORKS written recipe lacks native feature owners")
    CheckProfile(CaseValue, Observed)
    CheckProgramOps(CaseValue, Observed)
    Bindings = Observed["parameter_bindings"]
    if set(Bindings) != set(CaseValue["parameters"]):
        raise ValueError("SOLIDWORKS written recipe lacks driving parameter witnesses")
    for ParamName, ParamValue in CaseValue["parameters"].items():
        Binding = Bindings[ParamName]
        Contract = Program["bindings"][ParamName]
        if (
            Binding["owner"] != Contract["owner"]
            or Binding["field"] != Contract["field"]
            or not isclose(Binding["value"], ParamValue, rel_tol=1e-9, abs_tol=1e-7)
        ):
            raise ValueError("SOLIDWORKS native parameter owner or value differs")
    ExpectedUnits = 3 if CaseValue["options"]["variant"] == "units-inch" else 5
    if Observed["units_code"] != ExpectedUnits:
        raise ValueError("SOLIDWORKS written recipe display unit witness differs")
