# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose

from CaptureTools.Catalogue.Recipes.ProgramCase import ProgramCase
from CaptureTools.Catalogue.SolidWorks.CheckProgramShape import CheckProgramShape


# every declared edit variant and native archive needs its own verified reopen witness
def CheckProgramReads(CaseValue, Observed):
    Program = CaseValue["options"]["program"]
    Prefix = CaseValue["recipe"] + "-solidworks-"
    Expected = {
        Prefix + "baseline-a.SLDPRT": CaseValue,
        Prefix + "baseline-b.SLDPRT": CaseValue,
    }
    if Observed["fresh_reopen"]["open_status"] != {"errors": 0, "warnings": 0}:
        raise ValueError("SOLIDWORKS written baseline reopened with diagnostics")
    for Reading in (
        Observed["baseline"],
        Observed["fresh_reopen"]["measurements"],
        Observed["unchanged_rebuild"],
    ):
        CheckProgramShape(CaseValue, Reading)
    Edits = {Edit["parameter"]: Edit for Edit in Program["edits"]}
    Seen = set()
    for Reading in Observed["edits"]:
        Parameter = Reading["parameter"]
        if Parameter not in Edits or Parameter in Seen:
            raise ValueError(
                "SOLIDWORKS written edit roster repeats or invents controls"
            )
        Seen.add(Parameter)
        Edit = Edits[Parameter]
        Changed = ProgramCase(CaseValue, Edit["parameters"])
        if not isclose(Reading["value"], Edit["value"], rel_tol=0, abs_tol=0):
            raise ValueError(
                "SOLIDWORKS written edit differs from the compiled challenge"
            )
        CheckProgramShape(Changed, Reading["edited"])
        CheckProgramShape(CaseValue, Reading["restored"])
        FileName = Reading["saved_file"]
        if FileName in Expected or not FileName.startswith(
            Prefix + "edit-" + Parameter + "-"
        ):
            raise ValueError("SOLIDWORKS written edit has an invalid archive identity")
        Expected[FileName] = Changed
    if Seen != set(CaseValue["parameters"]) or Seen != set(Edits):
        raise ValueError("SOLIDWORKS written recipe lacks independent driving edits")
    Variants = {Variant["name"]: Variant for Variant in Program["variants"]}
    Seen = set()
    for Reading in Observed["variants"]:
        Name = Reading["variant"]
        if Name not in Variants or Name in Seen:
            raise ValueError(
                "SOLIDWORKS written variant roster repeats or invents controls"
            )
        Seen.add(Name)
        Variant = Variants[Name]
        Changed = ProgramCase(CaseValue, Variant["parameters"], Variant["options"])
        CheckProgramShape(Changed, Reading["reading"])
        FileName = Prefix + Name + ".SLDPRT"
        if FileName in Expected:
            raise ValueError("SOLIDWORKS written variant repeats an archive")
        Expected[FileName] = Changed
    if Seen != set(Variants) or set(Observed["reopened_files"]) != set(Expected):
        raise ValueError(
            "SOLIDWORKS written recipe lacks its complete native reopen roster"
        )
    for FileName, Reading in Observed["reopened_files"].items():
        if Reading["open_status"] != {"errors": 0, "warnings": 0}:
            raise ValueError("SOLIDWORKS written archive reopened with diagnostics")
        CheckProgramShape(Expected[FileName], Reading)
    return set(Expected)
