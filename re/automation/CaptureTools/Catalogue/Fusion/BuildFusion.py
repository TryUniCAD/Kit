# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Fusion.FusionCases import KFusionDefaults
from CaptureTools.Catalogue.Fusion.FusionParams import ValidateFusion


# dependency ordering avoids invalid intermediate pocket and annular profile dimensions
def ParamOrder(Case):
    Recipe, Parameters = Case["recipe"], Case["parameters"]
    Order = []
    for ParamName, ParamValue in Parameters.items():
        Original = KFusionDefaults[Recipe][ParamName]
        Restricted = ParamName.startswith("cut_") or ParamName == "inner_radius_mm"
        First = (Restricted and ParamValue <= Original) or (
            not Restricted and ParamValue >= Original
        )
        Order.append((0 if First else 1, ParamName))
    return [ParamName for _, ParamName in sorted(Order)]


# new cases reuse actual native builders without changing sealed historical capture code
def BuildFusion(Helper, Application, Case):
    Normal = ValidateFusion(Case)
    Document = Helper["BUILDERS"][Normal["recipe"]](Application, Normal["options"])
    Design = Helper["design_of"](Document)
    for ParamName in ParamOrder(Normal):
        Parameter = Design.allParameters.itemByName(ParamName)
        if Parameter is None:
            raise RuntimeError(
                f"the native builder omitted driving parameter {ParamName}"
            )
        UnitName = "deg" if ParamName == "angle_deg" else "mm"
        Parameter.expression = f"{(-1 if ParamName in ('depth_mm', 'cut_depth_mm') and Parameter.value < 0 else 1) * Normal['parameters'][ParamName]:.17g} {UnitName}"
    if Design.computeAll() is not True:
        raise RuntimeError("fusion refused the requested parameterized rebuild")
    return Document
