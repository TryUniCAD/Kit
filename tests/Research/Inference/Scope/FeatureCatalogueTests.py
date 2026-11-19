# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
from pathlib import Path

from pytest import mark

from tests.Research.Inference.Scope.FeatureHandoffTests import InvokeAutomation


# catalogue plans must come through the same public command the planner invokes
def Generate(PathValue, *Arguments, Expected=0):
    return InvokeAutomation(
        "InferenceGrid/FeatureDispatch.py",
        "--catalogue",
        PathValue,
        *Arguments,
        Expected=Expected,
    )


# a small catalogue exercises supported and unsupported options without native dependencies
def CatalogueFixture():
    return {
        "schema_version": 1,
        "waves": [{"id": "alpha"}],
        "families": [
            {
                "id": "family:extrude",
                "parent_id": None,
                "wave": "alpha",
                "dependencies": [],
                "subfeatures": [
                    {
                        "id": "family:extrude:cut-extrude",
                        "dependencies": [],
                        "options": ["through all"],
                    },
                    {
                        "id": "family:extrude:boss-base-extrude",
                        "dependencies": [],
                        "options": ["blind"],
                    },
                    {
                        "id": "family:extrude:surface-extrude",
                        "dependencies": [],
                        "options": ["offset", "depth"],
                    },
                ],
            }
        ],
    }


# each feature identity must remain stable across input ordering and repeated generation
def CheckDeterministicCatalogue(TmpPath: Path):
    Value = CatalogueFixture()
    Catalogue = TmpPath / "Catalogue.json"
    Catalogue.write_text(json.dumps(Value), encoding="utf-8")
    Pin = hashlib.sha256(Catalogue.read_bytes()).hexdigest()
    Output = Generate(Catalogue, "--catalogue-sha256", Pin, "manifest")
    assert Generate(Catalogue, "manifest") == Output
    Initial = json.loads(Output)
    assert Initial["catalogue_sha256"] == Pin
    Features = Initial["features"]
    assert Features["family:extrude:cut-extrude"]["route"]["recipe"] == "P04"
    assert Features["family:extrude:boss-base-extrude"]["route"]["recipe"] == "P03"

    Value["families"][0]["subfeatures"].reverse()
    Value["families"][0]["subfeatures"][0]["options"].reverse()
    Catalogue.write_text(json.dumps(Value), encoding="utf-8")
    Reordered = json.loads(Generate(Catalogue, "manifest"))
    assert Reordered["catalogue_sha256"] != Pin
    assert Reordered["features"] == Features
    assert "SHA-256" in Generate(
        Catalogue, "--catalogue-sha256", Pin, "manifest", Expected=1
    )

    Feature = "family:extrude:surface-extrude"
    Store = TmpPath / "UnopenedStore"
    Blocked = json.loads(
        Generate(Catalogue, "--feature", Feature, "--store", Store, "submit")
    )
    assert Blocked["status"] == "blocked" and Blocked["route"] is None
    assert Blocked["blockers"] and not Store.exists()


# invalid references and repeated identities must fail before producing a dispatch plan
@mark.parametrize("Fault", ("repeat", "missing", "cycle"))
def CheckInvalidCatalogue(TmpPath: Path, Fault: str):
    Value = CatalogueFixture()
    Family = Value["families"][0]
    if Fault == "repeat":
        Family["subfeatures"].append(Family["subfeatures"][0])
    else:
        Family["dependencies"].append(
            "family:extrude" if Fault == "cycle" else "family:absent"
        )
    Catalogue = TmpPath / "Catalogue.json"
    Catalogue.write_text(json.dumps(Value), encoding="utf-8")
    assert "catalogue feature dispatch refused" in Generate(
        Catalogue, "manifest", Expected=1
    )
