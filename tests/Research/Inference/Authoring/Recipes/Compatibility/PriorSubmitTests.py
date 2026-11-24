# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.CliResearch.OpenLegacy import OpenLegacy
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.RunCatalogue import RunCatalogue
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe


# previously committed submission code must create a store that the candidate reuses without replacing any original job definitions
def CheckPriorJobs(TmpPath: FilePath) -> None:
    Prepared = RunCatalogue(TmpPath, "--capture-mode", "discovery")
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    PlanPath = TmpPath / "Run/AuthoringPlan.json"
    PlanValue = DecodeJson(PlanPath.read_bytes())
    del PlanValue["solidworks_batch_version"]
    _ = PlanPath.write_text(EncodeJson(PlanValue), encoding="utf-8")
    Payload = {"directory": str(TmpPath / "Queue"), "plan": str(PlanPath)}
    with OpenLegacy(
        KRepoRoot, TmpPath, "66d4f5b856833833bbf67fe62a61c3450d8dc76f"
    ) as Checkout:
        Populated = RunProcess(
            ["git", "-C", str(Checkout), "sparse-checkout", "add", "tests"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert Populated.returncode == 0, Populated.stderr
        Previous = RunProbe(TmpPath, "submit", Payload, RootPath=Checkout)
        assert Previous.returncode == 0, Previous.stderr
        Before = DecodeJson(Previous.stdout)
    Current = RunProbe(TmpPath, "submit", Payload)
    assert Current.returncode == 0, Current.stderr
    assert DecodeJson(Current.stdout) == Before
