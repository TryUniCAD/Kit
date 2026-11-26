# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from json import loads as ParseJson
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as MakeFolder

from pytest import mark as MarkCases

from tests.Research.Archives.SolidWorksFreshBossTests import KFreshContext
from tests.Research.Archives.VisualState.VisualStateProcess import (
    KSourceFreeProgram,
    RunVisualCase,
)

# each owner needs a typed visibility choice for independent refusal cases
KVisibility = {
    "holder": True,
    "26": False,
    "5": True,
    "2": False,
    "3": True,
    "4": False,
}

# every owner receives an explicit caller choice rather than a captured or guessed visibility default
KVisualSettings = {
    "representation_id": 37,
    "name": "independent hidden profile Ω",
    "visibility": KVisibility,
}


# complete fresh packages must preserve the existing feature graph and every unrelated metadata member
def LoadAuthored(Destination: FilePath) -> None:
    Result = RunVisualCase(
        KSourceFreeProgram, [KFreshContext, KVisualSettings, str(Destination)]
    )
    assert Result.returncode == 0, Result.stderr
    Report = ParseJson(Result.stdout)
    assert DigestBytes(Destination.read_bytes()).hexdigest() == Report["archive_sha256"]
    assert Report["stream_count"] == 33
    assert Report["dimensions_mm"] == [38.25, 22.5, -7.75]
    assert Report["visual_state"]["visibility"] == KVisualSettings["visibility"]
    assert Report["visual_state"]["representation_id"] == 37
    assert Report["visual_state"]["appearance_id"] == 99
    assert Report["visual_state"]["feature_clocks"] == {
        "26": 1783600227,
        **{str(Identity): 1783600226 for Identity in (2, 3, 4, 5)},
    }
    assert Report["native_acceptance"] is False
    Existing = b"user owned existing destination"
    _ = Destination.write_bytes(Existing)
    Retry = RunVisualCase(
        KSourceFreeProgram, [KFreshContext, KVisualSettings, str(Destination)]
    )
    assert Retry.returncode != 0
    assert "already exists" in Retry.stderr
    assert Destination.read_bytes() == Existing


# temporary publication exercises the full candidate lifecycle without retaining user workspace artifacts
def CheckPackage() -> None:
    with MakeFolder() as TempRoot:
        LoadAuthored(FilePath(TempRoot) / "AuthoredVisual.SLDPRT")


# incomplete or foreign owner choices cannot silently become a seemingly valid native candidate
@MarkCases.parametrize(
    "Visibility",
    [
        {"holder": True},
        {**KVisibility, "81": True},
        {**KVisibility, "26": 1},
    ],
)
def CheckRefusal(Visibility: dict[str, object]) -> None:
    with MakeFolder() as TempRoot:
        Destination = FilePath(TempRoot) / "RejectedVisual.SLDPRT"
        Result = RunVisualCase(
            KSourceFreeProgram,
            [
                KFreshContext,
                {**KVisualSettings, "visibility": Visibility},
                str(Destination),
            ],
        )
        assert Result.returncode != 0
        assert "visual-state verification failed" in Result.stderr
        assert not Destination.exists()


# sealed controls check the recovered grammar without admitting them as construction templates
def CheckCorpus() -> None:
    Program = "from runpy import run_path; import sys; sys.argv = ['VerifyVisualState.py', '--replay-corpus']; run_path('re/solidworks/WriterResearch/VisualState/VerifyVisualState.py', run_name='__main__')"
    Result = RunVisualCase(Program, None)
    assert Result.returncode == 0, Result.stderr
    Report = ParseJson(Result.stdout)
    assert Report["capture_revision"] == "466dcb172dfa3803463e07ccde963ba01671d200"
    assert len(Report["controls"]) == 8
    assert all(
        Entry["bytes"] == 1789 and Entry["owners"] == 6 for Entry in Report["controls"]
    )
    assert Report["native_acceptance"] is False
