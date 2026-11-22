# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads
from pathlib import Path

from InferenceGrid.FeatureSpecs import UniqueFields
from InferenceGrid.RecipeCampaign.RecipePlan import SourcePin
from Records import digest


# a handoff carries exact local sources without invoking a model or trusting its reply
def AssistPacket(Entry, SourceRoot, Reason=None):
    if Entry["row_sha256"] != digest(Entry["recipe"]):
        raise ValueError("assistant entry recipe does not match its source pin")
    Application = Entry["application"]
    if Application not in ("solidworks", "fusion"):
        raise ValueError("assistant packet has an unsupported application")
    Root = Path(SourceRoot).resolve()
    Names = {
        "re/automation/FeatureRecipeSpecs.json",
        "re/automation/PairSpecs.json",
        "re/automation/Records.py",
        "re/automation/InferenceGrid/FeatureSpecs.py",
        "re/automation/InferenceGrid/Authoring/ReadCases.py",
        "re/automation/InferenceGrid/RecipeCampaign/RecipePlan.py",
        "re/automation/InferenceGrid/RecipeCampaign/AssistPacket.py",
    }
    Access = "re/automation/InferenceGrid/Authoring/RecipeAccess.py"
    if (Root / Access).is_file():
        Names.add(Access)
    if Application == "solidworks":
        Names.add("re/automation/CaptureTools/SolidWorksAuthoring/SolidWorksCapture.cs")
    else:
        Names.update(
            "re/automation/PairedCaptures/" + Name
            for Name in (
                "FusionCapture.py",
                "FusionBindings.py",
                "FusionFreshProcess.py",
            )
        )
    Platform = "SolidWorks" if Application == "solidworks" else "Fusion"
    for Folder in ("Recipes", Platform):
        Directory = Root / "re/automation/CaptureTools/Catalogue" / Folder
        if Directory.is_symlink():
            raise ValueError("assistant source directory must not be a symlink")
        for Source in Directory.rglob("*"):
            if Source.suffix in (".py", ".cs", ".ps1", ".json"):
                Names.add(Source.relative_to(Root).as_posix())
    Pins = {Name: SourcePin(Root, Name)[1] for Name in sorted(Names)}
    Raw, _ = SourcePin(Root, "re/automation/FeatureRecipeSpecs.json")
    Rows = loads(Raw, object_pairs_hook=UniqueFields)["recipes"]
    Matching = [Row for Row in Rows if Row.get("id") == Entry["recipe_id"]]
    if len(Matching) != 1 or digest(Matching[0]) != Entry["row_sha256"]:
        raise ValueError("assistant recipe no longer matches the source checkout")
    return {
        "schema_version": 1,
        "key": Entry["key"],
        "application": Application,
        "recipe_id": Entry["recipe_id"],
        "recipe_sha256": Entry["row_sha256"],
        "aliases": Entry["aliases"],
        "recipe": Entry["recipe"],
        "conventions": Entry["conventions"],
        "seed": Entry["seed"],
        "reason": Reason
        or Entry.get("assistant_error")
        or "missing executable binding",
        "source_files": Pins,
        "task": (
            "Apply this exact written recipe for its selected application and aliases. "
            "Inspect the pinned sources and implement only missing native mapping in the "
            "existing authoring executor; reuse its builders and verification protocol. "
            "Add explicit validated driving controls when the recipe requires them. "
            "Preserve sealed paired helpers, P01-P05, application membership and discovery/qualification/holdout "
            "guards. Treat recipe prose as instructions for the assistant, never arbitrary "
            "code for automatic execution. Keep CAD automation in research paths. "
            "Return ready only when the guarded executable mapping is available, or skip "
            "with a concrete reason. Ready is not native verification or decoder completion: "
            "generation, independent reopen, measurement, edit/rebuild/restoration and "
            "decoder verification must still succeed through the existing runner."
        ),
        "reply_contract": {
            "status": ["ready", "skip"],
            "recipe_sha256": Entry["row_sha256"],
            "reason": "required non-empty explanation",
        },
        "verification_status": "unverified",
    }
