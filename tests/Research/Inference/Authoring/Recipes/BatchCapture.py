# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as ImportPaths

ImportPaths.insert(0, str(FilePath(__file__).resolve().parents[5]))

from tests.Research.Inference.Authoring.Contracts.ResolveSession import ResolveSession

from tests.Research.Inference.Authoring.Contracts.ArtifactData import (
    ArtifactData,
    MemberData,
)
from tests.Research.Inference.Authoring.Recipes.ReadFixture import ReadFixture
from tests.Research.Inference.Authoring.Recipes.WriteBundle import WriteBundle


# retained controls exercise real batch artifact transport without claiming native authoring acceptance
def PublishBatch(SessionPath: FilePath) -> None:
    Packet = DecodeJson((SessionPath / "job.json").read_bytes())
    Content = ReadFixture(SessionPath, Packet["inputs"]["source"])
    Fault = Packet["job"]["options"]["fault"]
    Bundles: dict[str, dict[str, MemberData]] = {}
    Artifacts: dict[str, ArtifactData] = {}
    for Label in ("First",) if Fault == "native-rejected" else ("First", "Second"):
        Current = Fault if Label == "Second" else "normal"
        Members, Artifact = WriteBundle(SessionPath, Label, Content, Current)
        Artifacts["bundle." + Label.lower()] = Artifact
        if Current != "missing":
            Bundles["bundle." + Label.lower()] = (
                Bundles["bundle.first"] if Current == "swapped" else Members
            )
    Records: dict[str, object] = {
        "fixture_only": True,
        "native_acceptance": False,
        "application": "fusion",
        "bundles": Bundles,
    }
    if Fault == "native-rejected":
        Records["source_pins"] = {"fixture_only": True}
        Records["cases"] = {
            "fusion:second": {
                "case": {"recipe": "fixture", "parameters": {}, "options": {}},
                "native_verified": False,
                "native_rejection": "fixture measurement mismatch",
            },
        }
    Result = {
        "outcome": "completed",
        "reason": "fixture transport of retained native controls only",
        "records": Records,
        "artifacts": Artifacts,
    }
    _ = (SessionPath / "result.json").write_text(
        EncodeJson(Result, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    PublishBatch(ResolveSession(ArgValues[1]))
