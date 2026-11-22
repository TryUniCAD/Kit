# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Fusion.CheckFusion import CheckFusion
from CaptureTools.Catalogue.Fusion.FusionBatch import ModelCase
from CaptureTools.Catalogue.Fusion.FusionEdits import EditCases


# edited archives must independently reopen before a successful parameter witness is recorded
def CaptureEdits(Helper, Fresh, Application, Document, Case, Output, Owned):
    Design = Helper["design_of"](Document)
    Results = []
    for Edit in EditCases(Case):
        ParamName = Edit["parameter"]
        Parameter = Design.allParameters.itemByName(ParamName)
        if Parameter is None:
            raise RuntimeError(f"fusion lost editable driving parameter {ParamName}")
        Original = Parameter.expression
        UnitName = "deg" if ParamName == "angle_deg" else "mm"
        Result = {"parameter": ParamName, "value": Edit["value"], "case": Edit["case"]}
        try:
            Parameter.expression = f"{Edit['value']:.17g} {UnitName}"
            Result["changed"] = CheckFusion(Helper, Document, Edit["case"])
            ArchiveName = f"{Case['id']}-edit-{ParamName}.f3d"
            Result["archive"] = Fresh["save_archive"](
                Helper, Document, Output, ArchiveName
            )
        finally:
            Parameter.expression = Original
            Result["restored"] = CheckFusion(Helper, Document, ModelCase(Case))
        Reopened = Helper["reopen"](Application, Output / ArchiveName, Owned)
        try:
            Result["reopened"] = CheckFusion(Helper, Reopened, Edit["case"])
        finally:
            Helper["close"](Reopened, Owned)
            Fresh["checked_bytes"](Output / ArchiveName, Result["archive"])
        Results.append(Result)
    return Results


# the second process verifies actual first process bytes before generating edit evidence
def CaptureReadback(Helper, Fresh, Application, Case, Prior, Output, Owned):
    Baseline = Prior["archive"]
    ArchiveName = f"{Case['id']}-baseline.f3d"
    Source = Output.parent / "phase-a" / ArchiveName
    if Baseline["file"] != ArchiveName:
        raise RuntimeError("fusion phase a baseline name differs from its case")
    Content = Fresh["checked_bytes"](Source, Baseline)
    Replayed = Output / ArchiveName
    Fresh["write_new"](Replayed, Content)
    Fresh["checked_bytes"](Replayed, Baseline)
    Document = Helper["reopen"](Application, Replayed, Owned)
    try:
        Reopened = CheckFusion(Helper, Document, ModelCase(Case))
        if Helper["design_of"](Document).computeAll() is not True:
            raise RuntimeError("fusion refused the independent fresh rebuild")
        Rebuilt = CheckFusion(Helper, Document, ModelCase(Case))
        Archive = dict(Baseline)
        Edits = CaptureEdits(Helper, Fresh, Application, Document, Case, Output, Owned)
        return {
            "id": Case["id"],
            "case": ModelCase(Case),
            "reopened": Reopened,
            "rebuilt": Rebuilt,
            "archive": Archive,
            "edits": Edits,
        }
    finally:
        Helper["close"](Document, Owned)
        Fresh["checked_bytes"](Source, Baseline)
        Fresh["checked_bytes"](Replayed, Baseline)
