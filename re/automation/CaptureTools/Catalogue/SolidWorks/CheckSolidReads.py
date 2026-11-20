# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.SolidWorks.CheckSolidShape import CheckSolidShape


# every saved edit and variant needs an independently measured native reopen
def CheckSolidReads(CaseValue, Observed):
    RecipeKey = CaseValue["recipe"]
    Params = CaseValue["parameters"]
    Options = CaseValue["options"]
    Prefix = RecipeKey + "-solidworks-"
    Expected = {
        Prefix + "baseline-a.SLDPRT": CaseValue,
        Prefix + "baseline-b.SLDPRT": CaseValue,
    }
    CheckSolidShape(CaseValue, Observed["baseline"])
    CheckSolidShape(CaseValue, Observed["fresh_reopen"]["measurements"])
    CheckSolidShape(CaseValue, Observed["unchanged_rebuild"])
    SeenParams = set()
    for EditRow in Observed["edits"]:
        ParamName = EditRow["parameter"]
        if ParamName in SeenParams or ParamName not in Params:
            raise ValueError("SOLIDWORKS edit roster repeats or invents a parameter")
        SeenParams.add(ParamName)
        Current = Params[ParamName]
        Changed = Current * 1.1
        if ParamName == "angle_deg":
            Changed = Current / 2
        elif ParamName == "inner_radius_mm":
            Changed = (Current + Params["outer_radius_mm"]) / 2
        elif ParamName.startswith("cut_"):
            Changed = (Current + Params[ParamName[4:]]) / 2
        ChangedCase = {**CaseValue, "parameters": {**Params, ParamName: Changed}}
        CheckSolidShape(ChangedCase, EditRow["edited"])
        CheckSolidShape(CaseValue, EditRow["restored"])
        FileName = EditRow["saved_file"]
        if FileName in Expected:
            raise ValueError("SOLIDWORKS edits repeat a saved archive")
        Expected[FileName] = ChangedCase
    RequiredParams = set(Params)
    if RecipeKey == "P04" and Options["termination"] == "through_all":
        RequiredParams.remove("cut_depth_mm")
    if SeenParams != RequiredParams:
        raise ValueError(
            "SOLIDWORKS authoring lacks a required independent driving edit"
        )
    Variants = {"units-inch": Options}
    if RecipeKey != "P05":
        Variants["plane-yz"] = {"basis": "YZ", "direction": 1, "termination": "blind"}
    if RecipeKey == "P03":
        Variants["direction-negative"] = {**Options, "direction": -1}
    if RecipeKey == "P04":
        Variants["termination-through-all"] = {**Options, "termination": "through_all"}
    SeenVariants = set()
    for VariantRow in Observed["variants"]:
        VariantName = VariantRow["variant"]
        if VariantName in SeenVariants or VariantName not in Variants:
            raise ValueError("SOLIDWORKS variant roster repeats or invents an option")
        SeenVariants.add(VariantName)
        VariantCase = {**CaseValue, "options": Variants[VariantName]}
        CheckSolidShape(VariantCase, VariantRow["reading"])
        Expected[Prefix + VariantName + ".SLDPRT"] = VariantCase
    if SeenVariants != set(Variants) or set(Observed["reopened_files"]) != set(
        Expected
    ):
        raise ValueError("SOLIDWORKS authoring lacks its complete native reopen roster")
    for FileName, Reopened in Observed["reopened_files"].items():
        if Reopened["open_status"] != {"errors": 0, "warnings": 0}:
            raise ValueError(
                "SOLIDWORKS saved archive reopened with native load diagnostics"
            )
        CheckSolidShape(Expected[FileName], Reopened)
    return set(Expected)
