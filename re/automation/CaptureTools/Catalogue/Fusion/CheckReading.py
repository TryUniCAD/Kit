# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import degrees, isclose, isfinite

from CaptureTools.Catalogue.Fusion.FusionExpected import ExpectFusion
from CaptureTools.Catalogue.Fusion.FusionParams import ValidateFusion
from CaptureTools.Catalogue.Fusion.FusionSketch import CheckSketch


# native reports must independently retain measured parameters geometry and executable history
def CheckReading(Reading, Case):
    Normal = ValidateFusion(Case)
    Expected = ExpectFusion(Normal)
    if Reading["design_type"] != "parametric" or not Reading["feature_tree"]:
        raise RuntimeError("fusion did not preserve the parametric feature tree")
    for Feature in Reading["feature_tree"]:
        if (
            Feature["health"]["state"] != "healthy"
            or Feature["suppressed"]
            or Feature["rolled_back"]
        ):
            raise RuntimeError("fusion reported an unhealthy or inactive feature")
    Parameters = {Parameter["name"]: Parameter for Parameter in Reading["parameters"]}
    if len(Parameters) != len(Reading["parameters"]):
        raise RuntimeError("fusion reported ambiguous parameter names")
    for ParamName, ParamValue in Normal["parameters"].items():
        Actual = Parameters.get(ParamName, {}).get("value_internal")
        if type(Actual) not in (int, float) or not isfinite(Actual):
            raise RuntimeError(f"fusion did not measure driving parameter {ParamName}")
        Actual = degrees(Actual) if ParamName == "angle_deg" else Actual * 10
        if not isclose(Actual, ParamValue, rel_tol=1e-9, abs_tol=1e-6):
            raise RuntimeError(
                f"fusion driving parameter differs from the request {ParamName}"
            )
    if Normal["recipe"] == "P04":
        for ParamName, Owner in (
            ("cut_center_u_mm", "width_mm"),
            ("cut_center_v_mm", "height_mm"),
        ):
            if Parameters.get(ParamName, {}).get("dependencies") != [Owner]:
                raise RuntimeError(
                    "fusion lost a live parent linked cut center expression"
                )
    if Reading["body_count"] != Expected["body_count"]:
        raise RuntimeError("fusion body count differs from the requested recipe")
    if len(Reading["bodies"]) != Expected["body_count"]:
        raise RuntimeError("fusion measured body roster differs from its body count")
    if "area_mm2" in Expected:
        Areas = Reading["sketches"][0]["profile_areas_mm2"]
        if not Areas or not isclose(
            max(Areas), Expected["area_mm2"], rel_tol=1e-9, abs_tol=1e-6
        ):
            raise RuntimeError(
                "fusion measured profile area differs from its driving geometry"
            )
    if Expected["body_count"]:
        if not all(Body["solid"] for Body in Reading["bodies"]):
            raise RuntimeError("fusion produced a nonsolid body")
        if not isclose(
            Reading["volume_mm3"], Expected["volume_mm3"], rel_tol=1e-9, abs_tol=1e-6
        ):
            raise RuntimeError("fusion volume differs from the independent expectation")
        if not all(
            isclose(Actual, Target, rel_tol=1e-9, abs_tol=1e-6)
            for Actual, Target in zip(
                Reading["center_of_mass_mm"], Expected["center_of_mass_mm"], strict=True
            )
        ):
            raise RuntimeError(
                "fusion center of mass differs from the independent expectation"
            )
    CheckSketch(Reading["sketches"], Normal)
    return {
        "status": "verified",
        "compute_all_return": True,
        "expected": Expected,
        "observed": Reading,
    }
