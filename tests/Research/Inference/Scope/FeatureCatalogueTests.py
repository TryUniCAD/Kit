# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
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

from tests.Research.Inference.Scope.FeatureHandoffTests import RunAutomation


# catalogue plans must come through the same public command the planner invokes
def Generate(PathValue: Path, *Arguments: str | Path, Expected: int = 0) -> str:
    return RunAutomation(
        "InferenceGrid/FeatureDispatch.py",
        "--catalogue",
        PathValue,
        *Arguments,
        Expected=Expected,
    )


# a small catalogue exercises supported and unsupported options without native dependencies
KCatalogue = Path(__file__).with_name("ExtrudeCatalogue.json")


# each feature identity must remain stable across input ordering and repeated generation
def CheckStablePlan(TmpPath: Path) -> None:
    Value = json.loads(KCatalogue.read_bytes())
    Catalogue = TmpPath / "Catalogue.json"
    _ = Catalogue.write_text(json.dumps(Value), encoding="utf-8")
    Digest = hashlib.sha256(Catalogue.read_bytes()).hexdigest()
    Output = Generate(Catalogue, "--catalogue-sha256", Digest, "manifest")
    assert Generate(Catalogue, "manifest") == Output
    Initial = json.loads(Output)
    assert Initial["catalogue_sha256"] == Digest
    Features = Initial["features"]
    assert Features["family:extrude:cut-extrude"]["route"]["recipe"] == "P04"
    assert Features["family:extrude:boss-base-extrude"]["route"]["recipe"] == "P03"

    Value["families"][0]["subfeatures"].reverse()
    Value["families"][0]["subfeatures"][0]["options"].reverse()
    _ = Catalogue.write_text(json.dumps(Value), encoding="utf-8")
    Reordered = json.loads(Generate(Catalogue, "manifest"))
    assert Reordered["catalogue_sha256"] != Digest
    assert Reordered["features"] == Features
    assert "SHA-256" in Generate(
        Catalogue, "--catalogue-sha256", Digest, "manifest", Expected=1
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
def CheckBadPlan(TmpPath: Path, Fault: str) -> None:
    Value = json.loads(KCatalogue.read_bytes())
    Family = Value["families"][0]
    if Fault == "repeat":
        Family["subfeatures"].append(Family["subfeatures"][0])
    else:
        Family["dependencies"].append(
            "family:extrude" if Fault == "cycle" else "family:absent"
        )
    Catalogue = TmpPath / "Catalogue.json"
    _ = Catalogue.write_text(json.dumps(Value), encoding="utf-8")
    assert "catalogue feature dispatch refused" in Generate(
        Catalogue, "manifest", Expected=1
    )


# the fusion snapshot includes timeline features and reviewed sketch methods
def CheckFusionPlan(TmpPath: Path) -> None:
    Catalogue = TmpPath / "Catalogue.sqlite"
    Status = ("unverified",) * 4
    Items = [
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
        _ = Database.execute(
            "CREATE TABLE items (id TEXT, kind TEXT, name TEXT, authoring_status TEXT, "
            + "decoding_status TEXT, writing_status TEXT, verification_status TEXT)"
        )
        _ = Database.executemany(
            "INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?)", Items
        )
        _ = Database.execute(
            "CREATE VIEW api_feature_types AS SELECT * FROM items WHERE kind='api_type'"
        )
    Previous = Catalogue.read_bytes()
    Digest = hashlib.sha256(Previous).hexdigest()
    Arguments = ("--fusion-catalogue", Catalogue, "--catalogue-sha256", Digest)
    Command = "InferenceGrid/FeatureDispatch.py"
    Output = RunAutomation(Command, *Arguments, "manifest")
    assert Output == RunAutomation(Command, *Arguments, "manifest")
    assert Catalogue.read_bytes() == Previous
    Features = json.loads(Output)["features"]
    assert Features[Items[0][0]]["route"]["scope"] == "p03-blind-boss.fusion"
    assert Features[Items[1][0]]["route"]["scope"] == "p01-corner-rectangle"
    assert Features[Items[1][0]]["qualification"]["decoding"] == "unverified"
    Store = TmpPath / "UnopenedStore"
    Blocked = json.loads(
        RunAutomation(
            Command, *Arguments, "--feature", Items[2][0], "--store", Store, "submit"
        )
    )
    assert Blocked["status"] == "blocked" and not Store.exists()


# the batch visits even a catalogue whose only feature has no reviewed route
def CheckUnmapped(TmpPath: Path) -> None:
    Catalogue = TmpPath / "Catalogue.json"
    PlanValue = json.loads(KCatalogue.read_bytes())
    Family = PlanValue["families"][0]
    Family["subfeatures"] = [Family["subfeatures"][-1]]
    _ = Catalogue.write_text(json.dumps(PlanValue), encoding="utf-8")
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
    assert Report["features"] == {"solidworks": {"awaiting_capture": 1}}
    assert Report["scopes"] == {} and not (RunPath / "OfflineSupervisor.log").exists()
