# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import loads
from math import isclose
from pathlib import Path

from CaptureTools.Catalogue.SolidWorks.CheckSolidReads import CheckSolidReads
from CaptureTools.Catalogue.SolidWorks.ValidateSolid import ValidateSolid
from CaptureTools.Catalogue.Recipes.RecipeRegistry import KRecipeBuilders


# native measurements need immutable archive and independent process witnesses before admission
def VerifySolid(CaseValue, OutputDirectory):
    CaseValue = ValidateSolid(CaseValue)
    OutputPath = Path(OutputDirectory).resolve(strict=True)
    RecipeKey = CaseValue["recipe"]
    RecipePath = OutputPath / RecipeKey
    CasePin = sha256((OutputPath / "ConfiguredCase.json").read_bytes()).hexdigest()
    Receipt = loads((RecipePath / "receipt.json").read_bytes())
    Measurements = (RecipePath / "measurements.json").read_bytes()
    Report = loads(Measurements)
    if "program" in CaseValue["options"] and (
        Report["written_recipe_sha256"]
        != CaseValue["options"]["program"]["recipe_sha256"]
        or Report["specifications_sha256"]
        != sha256(
            (
                Path(__file__).resolve().parents[3] / "FeatureRecipeSpecs.json"
            ).read_bytes()
        ).hexdigest()
    ):
        raise ValueError(
            "SOLIDWORKS written recipe source differs from its native receipt"
        )
    if (
        Receipt["recipe_id"] != RecipeKey
        or Receipt["errors"] != 0
        or Report["errors"] != []
        or Receipt["measurement_receipt_sha256"] != sha256(Measurements).hexdigest()
        or Receipt["configuration_sha256"] != CasePin
        or Report["configuration_sha256"] != CasePin
        or Report["configured_case"] != CaseValue
    ):
        raise ValueError("SOLIDWORKS authoring receipt or configured source mismatch")
    Owners = [
        loads((OutputPath / (PhaseName + "-owner.json")).read_bytes())
        for PhaseName in ("first", "second")
    ]
    Lifetimes = [
        loads((OutputPath / (PhaseName + "-native.json")).read_bytes())
        for PhaseName in ("first", "second")
    ]
    if (
        any(Owner["owned_process_exit_observed"] is not True for Owner in Owners)
        or Owners[0]["pid"] == Owners[1]["pid"]
        or Owners[0]["created"] >= Owners[1]["created"]
        or Report["authoring_process_id"] != Owners[0]["pid"]
        or Report["reopen_process_id"] != Owners[1]["pid"]
        or any(
            Native["pid"] != Owner["pid"]
            or Native["initial_documents"] != 0
            or Native["background_control"] is not True
            or Native["normal_exit_requested"] is not True
            or Native["cleanup_errors"] != []
            or "failure" in Native
            for Native, Owner in zip(Lifetimes, Owners, strict=True)
        )
    ):
        raise ValueError("SOLIDWORKS authoring lacks independent owned process exits")
    Observed = Report["observations"]
    Before = Observed["healthy_control_before"]
    After = Observed["healthy_control_after"]
    if (
        Before["native_sha256"] != After["native_sha256"]
        or Before["body_count"] != After["body_count"]
        or Before["body_count"] <= 0
        or not isclose(
            Before["volume_mm3"], After["volume_mm3"], rel_tol=1e-9, abs_tol=1e-6
        )
        or any(
            not isclose(First, Second, rel_tol=1e-9, abs_tol=1e-6)
            for First, Second in zip(
                Before["center_of_mass_mm"], After["center_of_mass_mm"], strict=True
            )
        )
    ):
        raise ValueError("SOLIDWORKS before and after controls disagree")
    Archives = []
    ExpectedFiles = CheckSolidReads(CaseValue, Observed)
    NativeFiles = Receipt["native_files"]
    Names = [NativeFile["file"] for NativeFile in NativeFiles]
    if (
        len(Names) != len(set(Names))
        or set(Names) != ExpectedFiles
        or Report["saves"] != NativeFiles
    ):
        raise ValueError(
            "SOLIDWORKS receipt differs from the complete native reopen roster"
        )
    for NativeFile in NativeFiles:
        FileName = NativeFile["file"]
        if Path(FileName).name != FileName or not FileName.startswith(
            RecipeKey + "-solidworks-"
        ):
            raise ValueError("SOLIDWORKS receipt archive name is outside the recipe")
        NativePath = RecipePath / FileName
        if (
            NativePath.is_symlink()
            or NativePath.resolve(strict=True).parent != RecipePath
        ):
            raise ValueError("SOLIDWORKS receipt archive escapes the recipe directory")
        Content = NativePath.read_bytes()
        if (
            len(Content) != NativeFile["size_bytes"]
            or sha256(Content).hexdigest() != NativeFile["sha256"]
            or NativeFile["save_errors"] != 0
            or NativeFile["save_warnings"] != 0
        ):
            raise ValueError(
                "SOLIDWORKS native archive differs from its accepted receipt"
            )
        Archives.append({**NativeFile, "path": str(NativePath)})
    Accepted = {
        "application": "solidworks",
        "case": CaseValue,
        "configuration_sha256": CasePin,
        "measurements": Report,
        "receipt": Receipt,
        "archives": Archives,
        "native_owners": Owners,
        "native_lifetimes": Lifetimes,
    }
    if "program" in CaseValue["options"]:
        Descriptor = KRecipeBuilders[RecipeKey]
        Accepted["recipe_scope"] = {
            "supported_variants": list(Descriptor["supported_variants"]),
            "unsupported_variants": list(Descriptor["unsupported_variants"]),
            "all_written_variations_verified": not Descriptor["unsupported_variants"],
        }
    return Accepted
