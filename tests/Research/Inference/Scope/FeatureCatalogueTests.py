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
import sqlite3

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


# the fusion snapshot includes timeline features and reviewed sketch methods
def CheckFusionCatalogue(TmpPath: Path):
    Catalogue = TmpPath / "Catalogue.sqlite"
    Status = ("unverified",) * 4
    Rows = [
        ("api:adsk.fusion.ExtrudeFeature", "api_type", "ExtrudeFeature", *Status),
        (
            "api:adsk.fusion.SketchLines.addTwoPointRectangle",
            "api_method",
            "addTwoPointRectangle",
            *Status,
        ),
        ("api:adsk.fusion.ArrangeFeature", "api_type", "ArrangeFeature", *Status),
    ]
    with sqlite3.connect(Catalogue) as Database:
        Database.execute(
            "CREATE TABLE items (id TEXT, kind TEXT, name TEXT, authoring_status TEXT, "
            "decoding_status TEXT, writing_status TEXT, verification_status TEXT)"
        )
        Database.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?)", Rows)
        Database.execute(
            "CREATE VIEW api_feature_types AS SELECT * FROM items WHERE kind='api_type'"
        )
    Previous = Catalogue.read_bytes()
    Pin = hashlib.sha256(Previous).hexdigest()
    Args = ("--fusion-catalogue", Catalogue, "--catalogue-sha256", Pin)
    Command = "InferenceGrid/FeatureDispatch.py"
    Output = InvokeAutomation(Command, *Args, "manifest")
    assert Output == InvokeAutomation(Command, *Args, "manifest")
    assert Catalogue.read_bytes() == Previous
    Features = json.loads(Output)["features"]
    assert Features[Rows[0][0]]["route"]["scope"] == "p03-blind-boss.fusion"
    assert Features[Rows[1][0]]["route"]["scope"] == "p01-corner-rectangle"
    assert Features[Rows[1][0]]["qualification"]["decoding"] == "unverified"
    Store = TmpPath / "UnopenedStore"
    Blocked = json.loads(
        InvokeAutomation(
            Command, *Args, "--feature", Rows[2][0], "--store", Store, "submit"
        )
    )
    assert Blocked["status"] == "blocked" and not Store.exists()


# the batch visits even a catalogue whose only feature has no reviewed route
def CheckRunUnmappedCatalogue(TmpPath: Path):
    Catalogue = TmpPath / "Catalogue.json"
    Plan = CatalogueFixture()
    Family = Plan["families"][0]
    Family["subfeatures"] = [Family["subfeatures"][-1]]
    Catalogue.write_text(json.dumps(Plan), encoding="utf-8")
    Run = TmpPath / "Run"
    InvokeAutomation(
        "InferenceGrid/RunFeatureCatalogue.py",
        "--directory",
        Run,
        "--solidworks-catalogue",
        Catalogue,
        Expected=2,
    )
    Report = json.loads((Run / "CatalogueResult.json").read_bytes())
    assert Report["status"] == "coverage_incomplete"
    assert Report["features"] == {"solidworks": {"recipe_unavailable": 1}}
    assert Report["scopes"] == {} and not (Run / "OfflineSupervisor.log").exists()
