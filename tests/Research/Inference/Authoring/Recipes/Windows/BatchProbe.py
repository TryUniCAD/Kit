# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as ImportPaths

ImportPaths.insert(0, str(FilePath(__file__).resolve().parents[6] / "re/automation"))

from CaptureTools.Catalogue.Recipes.CompileRecipe import CompileRecipe
from CaptureTools.Catalogue.SolidWorks.PrepareBatch import PrepareBatch


# native disk preparation can cross its real process boundary without entering an application runner
def PrepareInput() -> None:
    Payload = DecodeJson(FilePath(ArgValues[1]).read_bytes())
    Cases = [CompileRecipe(CaseValue) for CaseValue in Payload["cases"]]
    Prepared = PrepareBatch(Cases, Payload["directory"])
    print(
        EncodeJson(
            {
                **Prepared,
                "outputs": list(map(str, Prepared["outputs"])),
                "manifest": str(Prepared["manifest"]),
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    PrepareInput()
