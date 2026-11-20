# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from argparse import SUPPRESS
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[3] / "src"),
]

from CodexAdvice.AdviceOptions import add_options, read_options
from Corpus import git
from InferenceGrid.CatalogueBatch import KMaxBatchWorkers, RunCatalogueBatch
from InferenceGrid.FeatureCatalogue import ReadCatalogue
from InferenceGrid.FeatureFusionCatalogue import ReadFusionCatalogue
from Records import bounded, canonical, label
from Supervisor import bound_memory_reserve


# a single invocation owns catalogue planning and execution through its private controller
def MainRun():
    Parser = argparse.ArgumentParser(
        description="Run every mapped feature in one or both CAD catalogues",
        allow_abbrev=False,
    )
    Parser.add_argument("--input", type=Path, help="Inspect this CAD file and schedule feature experiments from its decoded structure")
    Parser.add_argument("--directory", required=True, type=Path)
    Parser.add_argument("--solidworks-catalogue", type=Path)
    Parser.add_argument("--solidworks-sha256")
    Parser.add_argument("--fusion-catalogue", type=Path)
    Parser.add_argument(
        "--catalogue", type=Path, help="Catalogue path for the kit run format"
    )
    Parser.add_argument(
        "--batch-format", choices=("fusion", "solidworks"), help=SUPPRESS
    )
    Parser.add_argument("--fusion-sha256")
    Parser.add_argument("--max-seconds", type=int, default=1200)
    Parser.add_argument(
        "--workers",
        type=int,
        metavar="N",
        help="Optional offline worker ceiling (default: automatic from memory and CPU)",
    )
    Parser.add_argument(
        "--reserved-memory-mib",
        type=int,
        metavar="MIB",
        help="Memory to keep free before launching a worker (offline default: 4096 MiB)",
    )
    Parser.add_argument("--native-config", type=Path)
    Parser.add_argument("--native-kind")
    Parser.add_argument("--native-resource")
    Parser.add_argument(
        "--native-ready",
        action="store_true",
        help="Mark the configured application resource ready in this run's new store",
    )
    add_options(Parser)
    Args = Parser.parse_args()
    try:
        Reserve = (
            None
            if Args.reserved_memory_mib is None
            else bound_memory_reserve(Args.reserved_memory_mib)
        )
        Advice = read_options(Args)
        if Advice is not None and os.name != "posix":
            raise ValueError("decoder advice requires macOS or Linux")
        FileAudit = None
        if Args.input:
            from InferenceGrid.FileScope import file_scope
            if not Args.batch_format or any((Args.catalogue, Args.solidworks_catalogue, Args.fusion_catalogue, Args.fusion_sha256, Args.solidworks_sha256)):
                raise ValueError("use --input with one kit run format and no catalogue options")
            with TemporaryDirectory() as Scratch:
                Catalogues, FileAudit = file_scope(Args.input, Args.batch_format, Path(Scratch), Path(__file__).resolve().parents[3])
        else:
            Catalogues = ReadRunInputs(Args)
        Native = ReadNativeOptions(Args)
        if Args.native_ready and Native is None:
            raise ValueError("--native-ready requires the native worker configuration")
        SourceRoot = Path(__file__).resolve().parents[3]
        Revision = git(SourceRoot, "rev-parse", "HEAD").decode("ascii").strip()
        Outcome = RunCatalogueBatch(
            Args.directory.resolve(),
            SourceRoot,
            Revision,
            Catalogues,
            bounded(Args.max_seconds, 1, 86400),
            Native,
            Advice,
            Reserve=Reserve,
            Workers=KMaxBatchWorkers if Args.workers is None else Args.workers,
            NativeReady=Args.native_ready,
            FileScope=FileAudit,
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
    Paths = {
        "solidworks": (
            Args.solidworks_catalogue,
            Args.solidworks_sha256,
            ReadCatalogue,
        ),
        "fusion": (Args.fusion_catalogue, Args.fusion_sha256, ReadFusionCatalogue),
    }
    if Args.batch_format:
        Other = "fusion" if Args.batch_format == "solidworks" else "solidworks"
        if any(Paths[Other][:2]):
            raise ValueError(
                f"kit run {Args.batch_format} only accepts its own catalogue"
            )
        del Paths[Other]
        Existing, Digest, Read = Paths[Args.batch_format]
        if Existing is not None and Args.catalogue is not None:
            raise ValueError("provide the catalogue path once")
        Paths[Args.batch_format] = (Args.catalogue or Existing, Digest, Read)
    elif Args.catalogue is not None:
        raise ValueError(
            "use --catalogue with kit run, or specify the catalogue format"
        )
    Catalogues = {}
    for Source, (PathValue, Pin, Read) in Paths.items():
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
