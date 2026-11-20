# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import math
from pathlib import Path
import subprocess
import sys

from tests.Research.Inference.Scope.FeatureHandoffTests import RunAutomation
from tests.Research.SupervisorClient import KRepoRoot

# a written recipe with a closed form volume exercises the full specification path
KWrittenFeature = "family:fillet:constant-radius-fillet"

# an identity that no recipe covers keeps the original planner blocker
KUnwrittenFeature = "family:fillet:unwritten-fillet"

# the reviewed cut route must keep its executable plan beside its paired recipe
KMappedFeature = "family:extrude:cut-extrude"


# one family holds written and unwritten recipes alongside mapped entries without native dependencies
def RecipeCatalogue(Features: dict[str, list[str]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "waves": [{"id": "alpha"}],
        "families": [
            {
                "id": Family,
                "parent_id": None,
                "wave": "alpha",
                "dependencies": [],
                "subfeatures": [
                    {"id": FeatureKey, "dependencies": [], "options": ["radius"]}
                    for FeatureKey in FeatureKeys
                ],
            }
            for Family, FeatureKeys in Features.items()
        ],
    }


# the catalogue file is written once per case so each command reads real bytes
def WriteCatalogue(TmpPath: Path, Features: dict[str, list[str]]) -> Path:
    Catalogue = TmpPath / "Catalogue.json"
    _ = Catalogue.write_text(json.dumps(RecipeCatalogue(Features)), encoding="utf-8")
    return Catalogue


# written recipes narrow the blocker while mapped and unwritten entries keep their states
def CheckRecipePlan(TmpPath: Path) -> None:
    Catalogue = WriteCatalogue(
        TmpPath,
        {
            "family:fillet": [KWrittenFeature, KUnwrittenFeature],
            "family:extrude": [KMappedFeature],
        },
    )
    Command = "InferenceGrid/FeatureDispatch.py"
    Features = json.loads(RunAutomation(Command, "--catalogue", Catalogue, "manifest"))[
        "features"
    ]
    Written = Features[KWrittenFeature]
    assert Written["status"] == "blocked" and Written["route"] is None
    assert Written["recipe_spec"] == "fillet-constant"
    assert Written["blockers"] == ["pinned_native_evidence_required"]
    Unwritten = Features[KUnwrittenFeature]
    assert "recipe_spec" not in Unwritten
    assert Unwritten["blockers"] == ["reviewed_recipe_and_pinned_evidence_required"]
    Mapped = Features[KMappedFeature]
    assert Mapped["status"] == "mapped" and Mapped["recipe_spec"] == "pair-through-cut"
    assert Mapped["route"]["recipe"] == "P04" and Mapped["blockers"] == []
    Store = TmpPath / "UnopenedStore"
    Blocked = json.loads(
        RunAutomation(
            Command,
            "--catalogue",
            Catalogue,
            "--feature",
            KWrittenFeature,
            "--store",
            Store,
            "submit",
        )
    )
    assert Blocked["blockers"] == ["pinned_native_evidence_required"]
    assert not Store.exists()


# the recipe command returns the readable authoring intent with evaluated volumes
def CheckRecipeCli() -> None:
    Command = "InferenceGrid/FeatureDispatch.py"
    Output = json.loads(RunAutomation(Command, "--feature", KWrittenFeature, "recipe"))
    assert Output["feature"] == KWrittenFeature
    assert Output["status"] == "awaiting_independent_authoring"
    Recipe = Output["recipe"]
    assert Recipe["id"] == "fillet-constant" and Recipe["seed"] == "block"
    assert Output["seed"]["volume_value_mm3"] == 8000
    assert math.isclose(Recipe["expect"]["volume_value_mm3"], 7960 + 10 * math.pi)
    assert math.isclose(Recipe["edit"]["volume_value_mm3"], 7910 + 22.5 * math.pi)
    Paired = json.loads(RunAutomation(Command, "--feature", KMappedFeature, "recipe"))
    assert Paired["recipe"]["pair_recipe"] == "P04" and Paired["seed"] is None
    assert "has no written recipe" in RunAutomation(
        Command, "--feature", KUnwrittenFeature, "recipe", Expected=2
    )


# the batch report separates entries that wait for capture from entries without recipes
def CheckWaitState(TmpPath: Path) -> None:
    Catalogue = WriteCatalogue(
        TmpPath, {"family:fillet": [KWrittenFeature, KUnwrittenFeature]}
    )
    RunPath = TmpPath / "Run"
    _ = RunAutomation(
        "InferenceGrid/RunFeatureCatalogue.py",
        "--directory",
        RunPath,
        "--solidworks-catalogue",
        Catalogue,
        Expected=2,
    )
    Report = json.loads((RunPath / "CatalogueResult.json").read_bytes())
    assert Report["status"] == "coverage_incomplete"
    assert Report["features"] == {
        "solidworks": {"awaiting_capture": 1, "recipe_unavailable": 1}
    }
    PlanValue = json.loads((RunPath / "CataloguePlan.json").read_bytes())
    Entry = PlanValue["features"]["solidworks"][KWrittenFeature]
    assert Entry["recipe_spec"] == "fillet-constant"
    assert Entry["blockers"] == ["pinned_native_evidence_required"]


# the checker validates the committed file and reports scoped entries without recipes
def CheckCoverage(TmpPath: Path) -> None:
    Command = "InferenceGrid/FeatureSpecs.py"
    Totals = json.loads(RunAutomation(Command))
    assert Totals["recipes"] > 0 and Totals["entries"] >= Totals["recipes"]
    Catalogue = WriteCatalogue(
        TmpPath,
        {
            "family:fillet": [KWrittenFeature, KUnwrittenFeature],
            "family:drawing": ["family:drawing:drawing-sheet"],
        },
    )
    Result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(KRepoRoot / "re/automation" / Command),
            "--solidworks-catalogue",
            str(Catalogue),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=150,
    )
    assert Result.returncode == 1, Result.stderr
    Coverage = json.loads(Result.stdout)["coverage"]["solidworks"]
    assert Coverage["in_scope"] == 2 and Coverage["written"] == 1
    assert Coverage["missing"] == [KUnwrittenFeature]
    assert KWrittenFeature not in Coverage["unknown"] and Coverage["unknown"]
