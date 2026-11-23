# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps
from pathlib import Path

from pytest import mark

from tests.Research.Inference.Authoring.SolidWorks.CompileCapture import CompileCapture


# independently specified inputs cross the real powershell and csharp compiler boundary
@mark.parametrize(
    "RecipeKey,Params,Basis,Direction,Termination",
    [
        ("P01", {"width_mm": 43, "height_mm": 17}, "XZ", 1, "blind"),
        ("P02", {"diameter_mm": 13}, "YZ", 1, "blind"),
        ("P03", {"width_mm": 45, "height_mm": 27, "depth_mm": 14}, "YZ", -1, "blind"),
        (
            "P04",
            {
                "width_mm": 45,
                "height_mm": 27,
                "depth_mm": 14,
                "cut_width_mm": 7,
                "cut_height_mm": 9,
                "cut_depth_mm": 5,
            },
            "XY",
            1,
            "through_all",
        ),
        (
            "P05",
            {
                "inner_radius_mm": 3,
                "outer_radius_mm": 8,
                "height_mm": 16,
                "angle_deg": 180,
            },
            "XZ",
            1,
            "blind",
        ),
    ],
)
def CheckCompiler(
    TmpPath: Path,
    RecipeKey: str,
    Params: dict[str, int],
    Basis: str,
    Direction: int,
    Termination: str,
) -> None:
    CasePath = TmpPath / "ConfiguredCase.json"
    OutputPath = TmpPath / "Capture"
    _ = CasePath.write_text(
        dumps(
            {
                "recipe": RecipeKey,
                "parameters": Params,
                "options": {
                    "basis": Basis,
                    "direction": Direction,
                    "termination": Termination,
                },
            }
        ),
        encoding="utf-8",
    )
    Process = CompileCapture(CasePath, OutputPath)
    assert Process.returncode == 0, Process.stderr
    assert "without starting an application" in Process.stdout
    assert not OutputPath.exists()


# invalid controls must be rejected by the compiled native boundary before application startup
@mark.parametrize("Fault", ("unknown", "negative", "radius", "reverse", "termination"))
def CheckRefusal(TmpPath: Path, Fault: str) -> None:
    Params = {
        "width_mm": 45,
        "height_mm": 27,
        "depth_mm": 14,
        "cut_width_mm": 7,
        "cut_height_mm": 9,
        "cut_depth_mm": 5,
    }
    Options = {"basis": "XY", "direction": 1, "termination": "blind"}
    if Fault == "unknown":
        Params["unexpected"] = 7
    elif Fault == "negative":
        Params["depth_mm"] = -1
    elif Fault == "radius":
        Params["cut_width_mm"] = 45
    elif Fault == "reverse":
        Options["direction"] = -1
    else:
        Options["termination"] = "guessed"
    CasePath = TmpPath / "ConfiguredCase.json"
    OutputPath = TmpPath / "Capture"
    _ = CasePath.write_text(
        dumps({"recipe": "P04", "parameters": Params, "options": Options}),
        encoding="utf-8",
    )
    Process = CompileCapture(CasePath, OutputPath)
    assert Process.returncode != 0
    assert not OutputPath.exists()
