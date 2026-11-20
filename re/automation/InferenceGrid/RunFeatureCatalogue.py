# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from pathlib import Path
import sqlite3
import subprocess
import sys

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[3] / "src"),
]

from Corpus import git
from InferenceGrid.CatalogueBatch import RunCatalogueBatch
from InferenceGrid.FeatureCatalogue import ReadCatalogue
from InferenceGrid.FeatureFusionCatalogue import ReadFusionCatalogue
from Records import bounded, canonical, label


# a single invocation owns catalogue planning and execution through its private controller
def MainRun():
    Parser = argparse.ArgumentParser(
        description="Run every mapped feature in one or both CAD catalogues"
    )
    Parser.add_argument("--directory", required=True, type=Path)
    Parser.add_argument("--solidworks-catalogue", type=Path)
    Parser.add_argument("--solidworks-sha256")
    Parser.add_argument("--fusion-catalogue", type=Path)
    Parser.add_argument("--fusion-sha256")
    Parser.add_argument("--max-seconds", type=int, default=1200)
    Parser.add_argument("--native-config", type=Path)
    Parser.add_argument("--native-kind")
    Parser.add_argument("--native-resource")
    Args = Parser.parse_args()
    try:
        Catalogues = ReadRunInputs(Args)
        Native = ReadNativeOptions(Args)
        SourceRoot = Path(__file__).resolve().parents[3]
        Revision = git(SourceRoot, "rev-parse", "HEAD").decode("ascii").strip()
        Outcome = RunCatalogueBatch(
            Args.directory.resolve(),
            SourceRoot,
            Revision,
            Catalogues,
            bounded(Args.max_seconds, 1, 86400),
            Native,
        )
        Output = canonical(
            {
                **Outcome,
                "result": str(Args.directory.resolve() / "CatalogueResult.json"),
            }
        )
        sys.stdout.buffer.write((Output + "\n").encode("utf-8"))
        return {"completed": 0, "coverage_incomplete": 2, "failed": 1}[
            Outcome["status"]
        ]
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as Error:
        Parser.exit(1, f"catalogue run refused: {Error}\n")


# both input formats retain their own source identities and optional pins
def ReadRunInputs(Args):
    Catalogues = {}
    for Source, PathValue, Pin, Read in (
        (
            "solidworks",
            Args.solidworks_catalogue,
            Args.solidworks_sha256,
            ReadCatalogue,
        ),
        ("fusion", Args.fusion_catalogue, Args.fusion_sha256, ReadFusionCatalogue),
    ):
        if PathValue is not None:
            Catalogues[Source] = Read(PathValue, Pin)
        elif Pin is not None:
            raise ValueError(f"{Source} SHA-256 requires its catalogue path")
    if not Catalogues:
        raise ValueError("provide at least one planner catalogue")
    return Catalogues


# native actions are only enabled through the host's supplied worker configuration
def ReadNativeOptions(Args):
    Options = (Args.native_config, Args.native_kind, Args.native_resource)
    if not any(Options):
        return None
    if not all(Options):
        raise ValueError(
            "native execution requires --native-config, --native-kind and --native-resource"
        )
    return Args.native_config, label(Args.native_kind), label(Args.native_resource)


if __name__ == "__main__":
    raise SystemExit(MainRun())
