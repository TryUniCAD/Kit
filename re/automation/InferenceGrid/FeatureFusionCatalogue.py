# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import closing
import hashlib
import sqlite3

from InferenceGrid.FeatureRoutes import DescribeRecipe, FeatureRecipes
from Records import digest, label

# offline catalogue reads have room for the published sqlite bundle
FusionCatalogueBytes = 64 * 1024 * 1024


# the sqlite snapshot keeps selected declarations bound to the bytes that were hashed
def ReadFusionCatalogue(CataloguePath, Expected):
    if not CataloguePath.is_file():
        raise ValueError("Fusion catalogue must be a regular SQLite file")
    with CataloguePath.open("rb") as Source:
        Raw = Source.read(FusionCatalogueBytes + 1)
    if len(Raw) > FusionCatalogueBytes or not Raw.startswith(b"SQLite format 3\0"):
        raise ValueError("invalid or oversized Fusion catalogue")
    Pin = hashlib.sha256(Raw).hexdigest()
    if Expected is not None and Expected != Pin:
        raise ValueError("catalogue SHA-256 does not match the expected input")
    with closing(sqlite3.connect(":memory:")) as Database:
        Database.deserialize(Raw)
        Database.execute("PRAGMA trusted_schema=OFF")
        Database.execute("PRAGMA query_only=ON")
        Features = FusionEntries(Database)
    return {
        "schema_version": 1,
        "catalogue_sha256": Pin,
        "catalogue_kind": "fusion-api-feature-types",
        "families": {},
        "features": Features,
    }


# reviewed sketch commands can be represented outside the timeline feature hierarchy
def FusionEntries(Database):
    Columns = "id,kind,name,authoring_status,decoding_status,writing_status,verification_status"
    Rows = Database.execute(
        f"SELECT {Columns} FROM api_feature_types ORDER BY id LIMIT 10001"
    ).fetchall()
    if not 1 <= len(Rows) <= 10000:
        raise ValueError("Fusion catalogue has an invalid feature type count")
    Rows += Database.execute(
        f"SELECT {Columns} FROM items WHERE id=? AND kind='api_method' LIMIT 2",
        ("api:adsk.fusion.SketchLines.addTwoPointRectangle",),
    ).fetchall()
    Features = {}
    for Identity, Kind, Name, *Qualification in Rows:
        Key = label(Identity)
        if (
            Key in Features
            or not Key.startswith("api:adsk.fusion.")
            or Kind not in {"api_type", "api_method"}
        ):
            raise ValueError(
                "Fusion catalogue contains a duplicate or invalid API identity"
            )
        Recipe = FeatureRecipes.get(Key)
        Plan = {
            "feature": Key,
            "api_kind": Kind,
            "name": Name,
            "status": "mapped" if Recipe else "blocked",
            "route": DescribeRecipe(Recipe) if Recipe else None,
            "blockers": (
                [] if Recipe else ["reviewed_recipe_and_pinned_evidence_required"]
            ),
            "qualification": dict(
                zip(
                    ("authoring", "decoding", "writing", "verification"),
                    Qualification,
                    strict=True,
                )
            ),
        }
        Features[Key] = {**Plan, "plan_id": digest(Plan)}
    return dict(sorted(Features.items()))
