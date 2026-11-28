# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from json import dumps as EncodeJson, loads as DecodeJson
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as ImportPaths

# isolated probes need the checkout test contracts beside the actual research modules
ImportPaths[:0] = [
    str(FilePath(__file__).resolve().parents[6] / "re/automation"),
    str(FilePath(__file__).resolve().parents[6]),
]

from tests.Research.Inference.Authoring.Contracts.CompiledCase import CompiledCase
from tests.Research.Inference.Authoring.Contracts.PreparedData import PreparedData

# the native compiler remains a runtime research import with an explicit returned case contract
KValidateSolid = CastValue(
    Callable[[object], CompiledCase],
    getattr(
        ImportModule("CaptureTools.Catalogue.SolidWorks.ValidateSolid"), "ValidateSolid"
    ),
)

# preparation preserves real filesystem paths while native applications remain outside this probe
KPrepareBatch = CastValue(
    Callable[[list[CompiledCase], object], PreparedData],
    getattr(
        ImportModule("CaptureTools.Catalogue.SolidWorks.PrepareBatch"), "PrepareBatch"
    ),
)


# native disk preparation can cross its real process boundary without entering an application runner
def PrepareInput() -> None:
    Payload = DecodeJson(ResolveTemp(ArgValues[1]).read_bytes())
    Cases = [KValidateSolid(CaseValue) for CaseValue in Payload["cases"]]
    Prepared = KPrepareBatch(Cases, ResolveTemp(Payload["directory"]))
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
