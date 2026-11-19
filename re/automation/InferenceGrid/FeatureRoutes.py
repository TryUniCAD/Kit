# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
def SubmitCut(Store, Revision):
    from InferenceGrid.Provision import ProvisionScope

    return ProvisionScope(Store, Revision)


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
def SubmitBoss(Store, Revision):
    from InferenceGrid.FeatureBoss import ProvisionBoss

    return ProvisionBoss(Store, Revision)


# the boss route reports its independent assessment and consequent rescans
def StatusBoss(Store):
    from InferenceGrid.FeatureBoss import ReadBoss
    from Ledger import Ledger

    with Ledger(Store) as State:
        return ReadBoss(State)


# the catalogue identity selects one bounded evidence scope per supported route
FeatureRecipes = {
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
