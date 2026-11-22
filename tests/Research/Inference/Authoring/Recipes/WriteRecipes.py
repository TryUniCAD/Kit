# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath

from tests.Research.Inference.Authoring.Recipes.RecipeTargets import (
    KExtraFeatures,
    KRecipeTargets,
)


# real planner inputs expose registered legacy and unsupported features in the same taxonomy
def WriteRecipes(TmpPath: FilePath) -> FilePath:
    Families: dict[str, list[dict[str, object]]] = {}
    for Feature in (*KRecipeTargets.values(), *KExtraFeatures):
        Family = Feature.rsplit(":", 1)[0]
        Families.setdefault(Family, []).append(
            {"id": Feature, "dependencies": [], "options": []}
        )
    Catalogue: dict[str, object] = {
        "schema_version": 1,
        "waves": [{"id": "alpha"}],
        "families": [
            {
                "id": Family,
                "wave": "alpha",
                "parent_id": None,
                "dependencies": [],
                "subfeatures": Features,
            }
            for Family, Features in Families.items()
        ],
    }
    CatalogPath = TmpPath / "FeaturePlan.json"
    _ = CatalogPath.write_text(EncodeJson(Catalogue), encoding="utf-8")
    return CatalogPath
