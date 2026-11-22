# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import executable as PythonExe
from tests.Research.Inference.Authoring.Recipes.WriteRecipes import WriteRecipes


# preparation fixtures must never represent licensed native measurements
def WriteInputs(TmpPath: FilePath) -> None:
    CatalogPath = WriteRecipes(TmpPath)
    Catalogue = DecodeJson(CatalogPath.read_bytes())
    Catalogue["families"].append(
        {
            "id": "family:planes",
            "wave": "alpha",
            "parent_id": None,
            "dependencies": [],
            "subfeatures": [
                {"id": "family:planes:offset-plane", "dependencies": [], "options": []}
            ],
        }
    )
    _ = CatalogPath.write_text(EncodeJson(Catalogue), encoding="utf-8")
    Metadata = {
        "application_build": "fixture-unlicensed",
        "api_metadata": {"fixture_only": True},
        "executable_file_version": "fixture-unlicensed",
        "executable_sha256": "0" * 64,
        "interop_sha256": "0" * 64,
    }
    _ = (TmpPath / "Api.json").write_text(EncodeJson(Metadata), encoding="utf-8")
    _ = (TmpPath / "Host.json").write_text(
        EncodeJson(
            {
                "executable": PythonExe,
                "interop_assembly": PythonExe,
                "native_environment": {},
            }
        ),
        encoding="utf-8",
    )
