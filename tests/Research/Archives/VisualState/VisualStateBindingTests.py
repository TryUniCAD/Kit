# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson

from pytest import mark as MarkCases

from tests.Research.Archives.SolidWorksFreshBossTests import KFreshContext
from tests.Research.Archives.VisualState.VisualStatePackageTests import KVisualSettings
from tests.Research.Archives.VisualState.VisualStateProcess import RunVisualCase

# complete authored package owners expose cross member inconsistencies that a stream only inverse cannot detect
KPackageSetup = """
import json
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "re/solidworks/WriterResearch"))
from CmgrBossMass import CalcBossMass
from OrdinaryConfig import BuildOrdinaryConfig
from OrdinaryPackage import BuildOrdinaryPackage
from ResolvedPart import BuildOrdinaryResolved
from VerifyFreshBoss import ParseContext, FixtureState, BuildPackageState
from VisualState.VisualStatePackage import MakePackageVisuals
from convert.adapters.solidworks.Container.Archive import ArchiveError
context, settings, rejection = json.load(sys.stdin)
bound, owners, metadata = FixtureState(ParseContext(json.dumps(context)))
config = BuildOrdinaryConfig(19000, owners.Config)
resolved = BuildOrdinaryResolved(19000, config, owners.System, bound.Profile, bound.Boss)
mass = CalcBossMass(bound.Bounds.Minimum, bound.Bounds.Maximum, owners.Config.First.DensityKgM3)
package = BuildPackageState(ParseContext(json.dumps(context)), owners, metadata, mass)
visual = MakePackageVisuals(package, bound.Profile, owners.System, settings["representation_id"], settings["name"], settings["visibility"])
"""


# valid individual records must still be refused when their document ownership or allocator binding is false
KPackageRefusals = """
if rejection == "configuration": visual = replace(visual, ConfigurationId=27)
if rejection == "feature": visual = replace(visual, Owners=(visual.Owners[0], replace(visual.Owners[1], FeatureId=97), *visual.Owners[2:]))
if rejection == "clock": visual = replace(visual, Owners=(visual.Owners[0], replace(visual.Owners[1], Created=1783600999), *visual.Owners[2:]))
if rejection == "appearance": visual = replace(visual, Owners=(replace(visual.Owners[0], Material=replace(visual.Owners[0].Material, AppearanceId=98)), *visual.Owners[1:]))
if rejection == "color": visual = replace(visual, Owners=(replace(visual.Owners[0], Material=replace(visual.Owners[0].Material, SurfaceColor=0x102030)), *visual.Owners[1:]))
if rejection == "allocator": package = replace(package, Definition=replace(package.Definition, AppearanceCounter=99))
try:
    BuildOrdinaryPackage(19000, owners.Config, config, resolved, bound.Profile, bound.Boss, replace(package, Visualization=visual))
except ArchiveError:
    print(json.dumps({"rejected": rejection}))
else:
    raise AssertionError("inconsistent visual binding accepted")
"""


# all mandatory ownership joins must run through the same complete package assembly used for native candidates
@MarkCases.parametrize(
    "Rejection",
    ["configuration", "feature", "clock", "appearance", "color", "allocator"],
)
def CheckBinding(Rejection: str) -> None:
    Result = RunVisualCase(
        KPackageSetup + KPackageRefusals, [KFreshContext, KVisualSettings, Rejection]
    )
    assert Result.returncode == 0, Result.stderr
    assert ParseJson(Result.stdout) == {"rejected": Rejection}
