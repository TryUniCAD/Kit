# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from Corpus import git
from InferenceGrid.FeatureCatalogue import ReadCatalogue
from InferenceGrid.FeatureSpecs import SpecFor
from Records import digest, read_record

# the first supported development scope excludes unimplemented direction and instance variations
KPlaneOptions = {"basis": "XY", "direction": 1, "instances": 1, "units": "mm"}


# jobs bind independent inputs before a generating model sees the discovery packet
def BuildJob(Args, SourceRoot, Advice):
    if Args.builder_feature != "family:planes:offset-plane":
        return (
            None,
            "verifier_support_missing: only the scoped offset-plane verifier is implemented",
        )
    if Args.solidworks_catalogue is None:
        return None, "prerequisite_missing: a SOLIDWORKS catalogue is required"
    Catalogue = ReadCatalogue(Args.solidworks_catalogue, None)
    if Args.builder_feature not in Catalogue["features"]:
        return (
            None,
            "prerequisite_missing: feature is absent from the selected catalogue",
        )
    Recipe = SpecFor(Args.builder_feature)
    if Recipe is None or Recipe["id"] != "plane-offset" or Recipe["seed"] != "block":
        return (
            None,
            "prerequisite_missing: exact written recipe and block seed are required",
        )
    if Advice is None:
        return (
            None,
            "generation_not_authorized: explicitly configure --advisor and authentication",
        )
    Metadata = (
        read_record(Args.builder_api_metadata) if Args.builder_api_metadata else None
    )
    if Metadata and "signatures" in Metadata:
        Metadata = {
            **Metadata,
            "application_build": ".".join(
                Metadata["executable_file_version"].split(".")[:3]
            ),
            "api_metadata": {
                "signatures": Metadata["signatures"],
                "enums": Metadata.get("enums", {}),
            },
            "documentation": [
                {
                    "url": "https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~InsertRefPlane.html",
                    "summary": "InsertRefPlane uses explicit reference constraints; the distance argument uses metres.",
                },
                {
                    "url": "https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IRefPlane~Transform.html",
                    "summary": "The native reference-plane transform exposes independently observable world placement.",
                },
            ],
        }
    if (
        not Metadata
        or not Metadata.get("application_build")
        or not Metadata.get("api_metadata")
    ):
        return None, "api_metadata_missing: supply the installed API metadata snapshot"
    Revision = git(SourceRoot, "rev-parse", "HEAD").decode().strip()
    SourceFile = SourceRoot / "re/automation/FeatureRecipeSpecs.json"
    Written = read_record(SourceFile)
    Discovery = [
        {"id": "D1", "offset_mm": 15, "edit_mm": 25},
        {"id": "D2", "offset_mm": 20, "edit_mm": 29},
        {"id": "D3", "offset_mm": 35, "edit_mm": 42},
    ]
    Job = {
        "schema_version": 1,
        "feature": Args.builder_feature,
        "application": "solidworks",
        "application_build": Metadata["application_build"],
        "application_fingerprint": digest(
            {
                Key: Metadata.get(Key)
                for Key in (
                    "executable_file_version",
                    "executable_sha256",
                    "interop_file_version",
                    "interop_sha256",
                )
            }
        ),
        "application_metadata": Metadata,
        "source_revision": Revision,
        "recipe": Recipe,
        "recipe_sha256": digest(Recipe),
        "prerequisites": {"block": Written["seeds"]["block"]},
        "supported_options": KPlaneOptions,
        "parameter_domain": {"offset_mm": [1, 60]},
        "recipe_file_sha256": sha256(SourceFile.read_bytes()).hexdigest(),
        "catalogue_sha256": Catalogue["catalogue_sha256"],
        "discovery_cases": Discovery,
        "sample_cases": [{"id": "S1", "offset_mm": 31, "edit_mm": 38}],
        "model": asdict(Advice),
        "limits": {
            "attempts": Args.builder_attempts,
            "seconds": Args.builder_seconds,
            "model_calls": Args.builder_model_calls,
            "call_seconds": Args.builder_call_seconds,
            "max_cost_usd": Args.builder_max_cost_usd,
        },
        "demo_defect": Args.builder_demo_defect,
        "negative_probe": Args.builder_negative_probe,
    }
    Job["id"] = "builder-development:" + digest(Job)
    from InferenceGrid.BuilderDevelopment.Verification.FreezeExpectations import (
        FreezeExpectations,
        VerifierPins,
    )

    Job["independent_verifier_sources"] = VerifierPins()
    Job["discovery_expectations_sha256"] = digest(
        FreezeExpectations(Discovery, Job["application_build"])
    )
    Job["id"] = "builder-development:" + digest(
        {Key: Value for Key, Value in Job.items() if Key != "id"}
    )
    return Job, None


# prompts contain discovery information only while reserved cases remain in the private controller
def ModelPacket(Job, Diagnostics):
    return {
        "feature": Job["feature"],
        "recipe": Job["recipe"],
        "prerequisites": Job["prerequisites"],
        "application": Job["application"],
        "application_build": Job["application_build"],
        "source_revision": Job["source_revision"],
        "supported_options": Job["supported_options"],
        "api_metadata": Job["application_metadata"]["api_metadata"],
        "documentation": Job["application_metadata"].get("documentation", []),
        "examples": [
            {
                "operation": "offset_plane",
                "support": "XY",
                "distance_expression": "scale * offset_mm * 0.001",
                "context": "trusted code creates the prerequisite block and collects observations",
            }
        ],
        "discovery_cases": Job["discovery_cases"],
        "diagnostics": Diagnostics,
    }
