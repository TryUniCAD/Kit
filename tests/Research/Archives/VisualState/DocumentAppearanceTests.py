# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkCases

from tests.Research.Archives.SolidWorksFreshBossTests import KFreshContext
from tests.Research.Archives.VisualState.VisualStatePackageTests import KVisualSettings
from tests.Research.Archives.VisualState.VisualStateProcess import (
    KCodecModel,
    KSourceFreeProgram,
    RunVisualCase,
)

# the native fixed gray shader must stay independent of the requested legacy color
KExplicitMaterial = KCodecModel + r"""
from CmgrVisualProfile import KExplicitProfile
from ColorAppearance import EncodeColorDspbr
locator = case["locator"]
explicit = replace(material, MaterialColor=material.SurfaceColor,
    NativeAssetPath=locator,
    BumpStrength=KExplicitProfile.BumpStrength,
    DisplacementDistance=KExplicitProfile.DisplacementDistance,
    UsesNormalMap=False, UsesDefaultAppearance=False)
state = replace(state, Owners=(replace(owners[0], Material=explicit), *owners[1:]))
generated = EncodeVisualState(19000, state)
decoded = DecodeVisualState(generated, 19000)
assert decoded.Owners[0].Material.NativeAssetPath == locator
assert EncodeVisualState(19000, decoded) == generated
if locator.startswith("<SystemTexture>"):
    try:
        RequireVisualFields(19000, explicit)
    except ArchiveError:
        pass
    else:
        raise AssertionError("normal package emission admitted a saved locator")
    try:
        RequireVisualFields(19000, replace(explicit, NativeAssetPath=locator.replace("Materials", "materials")),
            AllowSystemTexture=True)
    except ArchiveError:
        pass
    else:
        raise AssertionError("wrong native locator spelling accepted")
"""

# the native shader must reject the legacy color even when the locator passes validation
KIndependentShader = KExplicitMaterial + r"""
native_shader = EncodeColorDspbr(19000, 0xE4E4E4)
assert generated.count(native_shader) == 1
incorrect_shader = EncodeColorDspbr(19000, explicit.SurfaceColor)
try:
    DecodeVisualState(generated.replace(native_shader, incorrect_shader), 19000)
except ArchiveError as error:
    assert "fully typed ordinary color appearance fields" in str(error)
else:
    raise AssertionError("explicit appearance reused the legacy ColorRef as its shader")
"""


# arbitrary caller colors must survive all three ordinary owners during source free construction
@MarkCases.parametrize("Channels", [[139, 71, 203], [34, 149, 83]])
def CheckDocColor(Channels: list[int]) -> None:
    Settings = {**KVisualSettings, "document_rgb": Channels}
    Result = RunVisualCase(KSourceFreeProgram, [KFreshContext, Settings, None])
    assert Result.returncode == 0, Result.stderr
    Report = ParseJson(Result.stdout)
    assert Report["stream_count"] == 33
    assert Report["dimensions_mm"] == [38.25, 22.5, -7.75]
    assert Report["visual_state"]["document_rgb"] == Channels
    assert Report["visual_state"]["visibility"] == KVisualSettings["visibility"]
    assert Report["native_acceptance"] is False


# invalid components must fail before any native candidate can be published
@MarkCases.parametrize("Channels", [[0, True, 1], [0, 1, 256], [0, 1], None])
def CheckBadColor(TmpPath: FilePath, Channels: object) -> None:
    Candidate = TmpPath / "RejectedColor.SLDPRT"
    Settings = {**KVisualSettings, "document_rgb": Channels}
    Result = RunVisualCase(
        KSourceFreeProgram, [KFreshContext, Settings, str(Candidate)]
    )
    assert Result.returncode != 0
    assert "explicit document RGB" in Result.stderr
    assert not Candidate.exists()


# both locator contexts must retain the expected shader independently of the legacy color
@MarkCases.parametrize(
    "Locator",
    [
        r"C:\Fixture\data\graphics\materials\color.p2m",
        r"<SystemTexture>\graphics\Materials\color.p2m",
    ],
)
def CheckShader(Locator: str) -> None:
    Settings = {
        "appearance": 99,
        "visible": True,
        "mixed": False,
        "features": 1,
        "representation": 37,
        "name": "Independent color",
        "locator": Locator,
    }
    Result = RunVisualCase(KIndependentShader, Settings)
    assert Result.returncode == 0, Result.stderr
