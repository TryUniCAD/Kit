# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import partial
from typing import Callable, NamedTuple


# runner selection is fixed by reviewed code and never comes from catalogue text
class FeatureRecipe(NamedTuple):
    Scope: str
    Recipe: str
    Assessment: str
    Experiment: str | None
    Submit: Callable
    Status: Callable
    Advance: Callable | None


# cut submissions reuse the pinned paired scope and its two affected archives
def SubmitCut(Store, Revision, Dependencies=()):
    from InferenceGrid.Provision import ProvisionScope

    return ProvisionScope(Store, Revision, Dependencies)


# the cut status includes its attached native phase identities
def StatusCut(Store):
    from InferenceGrid.FeatureAdvance import ReadAssessment
    from Ledger import Ledger

    with Ledger(Store) as State:
        return ReadAssessment(State)[0]


# the two phase evidence transaction stays owned by the existing grid runner
def AdvanceCut(Store, Config, Kind, Resource, WaitSeconds):
    from InferenceGrid.FeatureAdvance import AdvanceEvidence

    return AdvanceEvidence(Store, Config, Kind, Resource, WaitSeconds)


# the boss route uses the retained solidworks signed depth archive cases
def SubmitBoss(Store, Revision, Application="solidworks", Dependencies=()):
    from InferenceGrid.FeatureBoss import ProvisionBoss

    return ProvisionBoss(Store, Revision, Application, Dependencies)


# the boss route reports its independent assessment and consequent rescans
def StatusBoss(Store, Application="solidworks"):
    from InferenceGrid.FeatureBoss import ReadBoss
    from Ledger import Ledger

    with Ledger(Store) as State:
        return ReadBoss(State, Application)


# bounds and driving dimensions can reuse the same measured corner rectangle cases
def SubmitRectangle(Store, Revision, Dependencies=()):
    from InferenceGrid.FeatureRectangle import SubmitRectangle as SubmitAssessment

    return SubmitAssessment(Store, Revision, Dependencies)


# aliases report one shared paired result regardless of the selected catalogue
def StatusRectangle(Store):
    from InferenceGrid.FeatureRectangle import StatusRectangle as ReadAssessment

    return ReadAssessment(Store)


# one discovery recipe keeps overlapping feature requests from duplicating work
RectangleRecipe = FeatureRecipe(
    "p01-corner-rectangle",
    "P01",
    "inference.paired-gap",
    None,
    SubmitRectangle,
    StatusRectangle,
    None,
)


# the catalogue identity selects one bounded evidence scope per supported route
FeatureRecipes = {
    "family:sketchlines:corner-rectangle": RectangleRecipe,
    "family:sketchdimensions:linear-dimension": RectangleRecipe,
    "family:sketchdimensions:driving-dimension": RectangleRecipe,
    "api:adsk.fusion.SketchLines.addTwoPointRectangle": RectangleRecipe,
    "api:adsk.fusion.ExtrudeFeature": FeatureRecipe(
        "p03-blind-boss.fusion",
        "P03",
        "inference.fields",
        None,
        partial(SubmitBoss, Application="fusion"),
        partial(StatusBoss, Application="fusion"),
        None,
    ),
    "family:extrude:boss-base-extrude": FeatureRecipe(
        "p03-blind-boss.solidworks",
        "P03",
        "inference.fields",
        None,
        SubmitBoss,
        StatusBoss,
        None,
    ),
    "family:extrude:cut-extrude": FeatureRecipe(
        "p04-through-all-body-selection",
        "P04",
        "inference.paired-gap",
        "fusion-two-body-through-all",
        SubmitCut,
        StatusCut,
        AdvanceCut,
    ),
}


# plan output describes research intent without serializing executable handlers
def DescribeRecipe(Recipe):
    return {
        "scope": Recipe.Scope,
        "recipe": Recipe.Recipe,
        "assessment_kind": Recipe.Assessment,
        "evidence_experiment": Recipe.Experiment,
    }
