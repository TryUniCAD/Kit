# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
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
    str(Path(__file__).resolve().parents[1] / "ApplicationWorkers"),
    str(Path(__file__).resolve().parents[3] / "src"),
]

from CodexAdvice.AdviceOptions import add_options, read_options
from Corpus import git
from InferenceGrid.CatalogueBatch import (
    KMaxBatchWorkers,
    ResumeCatalogue,
    RunCatalogueBatch,
)
from InferenceGrid.CatalogueRuntime import PauseCatalogue
from InferenceGrid.FeatureCatalogue import ReadCatalogue
from InferenceGrid.FeatureFusionCatalogue import ReadFusionCatalogue
from Records import bounded, canonical, label
from Supervisor import Busy, bound_memory_reserve


# a single invocation owns catalogue planning and execution through its private controller
def MainRun():
    Parser = argparse.ArgumentParser(
        description="Run every mapped feature in one or both CAD catalogues",
        allow_abbrev=False,
    )
    Parser.add_argument(
        "--input",
        type=Path,
        help="Inspect this CAD file and schedule feature experiments from its decoded structure",
    )
    Parser.add_argument(
        "--control",
        type=Path,
        action="append",
        default=[],
        help="Local SOLIDWORKS control part or raw binary comparison stream in auto mode (repeatable)",
    )
    Parser.add_argument("--directory", required=True, type=Path)
    Mode = Parser.add_mutually_exclusive_group()
    Mode.add_argument(
        "--pause",
        action="store_true",
        help="Let active jobs finish and stop taking new jobs",
    )
    Mode.add_argument(
        "--resume", action="store_true", help="Continue a prepared catalogue directory"
    )
    Parser.add_argument("--solidworks-catalogue", type=Path)
    Parser.add_argument("--solidworks-sha256")
    Parser.add_argument("--fusion-catalogue", type=Path)
    Parser.add_argument(
        "--catalogue", type=Path, help="Catalogue path for the kit run format"
    )
    Parser.add_argument(
        "--batch-format", choices=("fusion", "solidworks", "auto"), help=SUPPRESS
    )
    Parser.add_argument("--fusion-sha256")
    Parser.add_argument(
        "--max-seconds", type=int, help="Run time limit (new run default: 1200)"
    )
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
        "--author-samples",
        action="store_true",
        help="Author fresh executable recipe cases before decoding their native files",
    )
    Parser.add_argument(
        "--authoring-cases",
        type=Path,
        help="Explicit catalogue features and parameter overrides",
    )
    Parser.add_argument(
        "--capture-mode", choices=("discovery", "qualification", "holdout")
    )
    Parser.add_argument(
        "--authoring-grid",
        choices=("baseline", "three-values"),
        help="Generate a one-parameter-at-a-time ladder for every exposed driving quantity",
    )
    Parser.add_argument(
        "--solidworks-host",
        type=Path,
        help="Explicit installed executable and interop paths for owned SOLIDWORKS authoring",
    )
    Parser.add_argument(
        "--fusion-lifecycle",
        type=Path,
        help="Pinned owner lifecycle configuration for automatic Fusion restart and reopen",
    )
    Parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Write an authoring plan without native applications or controller jobs",
    )
    Parser.add_argument(
        "--native-ready",
        action="store_true",
        help="Mark the configured application resource ready in this run's new store",
    )
    Parser.add_argument(
        "--codec-request",
        type=Path,
        help="Qualify a reader or writer patch for this reviewed scope",
    )
    Parser.add_argument(
        "--codec-image", help="Local immutable Docker image ID for qualification"
    )
    Parser.add_argument("--codec-output", type=Path, help="New output patch file")
    Parser.add_argument(
        "--codec-candidate",
        type=Path,
        help="Use supplied replacements instead of Codex",
    )
    add_options(Parser)
    Args = Parser.parse_args()
    try:
        Promotion = (Args.codec_request, Args.codec_image, Args.codec_output)
        if (any(Promotion) or Args.codec_candidate) and not all(Promotion):
            raise ValueError("codec promotion requires request, image and output")
        if Args.pause and Args.codec_request:
            raise ValueError("codec promotion requires a running or resumed catalogue")
        SourceRoot = Path(__file__).resolve().parents[3]
        Directory = Args.directory.resolve()
        if Args.pause or Args.resume:
            CheckSavedArgs(Args)
            if Args.pause:
                sys.stdout.buffer.write(
                    (
                        canonical(
                            PauseCatalogue(Directory, SourceRoot, Args.batch_format)
                        )
                        + "\n"
                    ).encode("utf-8")
                )
                return 0
            Outcome = ResumeCatalogue(
                Directory,
                SourceRoot,
                Args.batch_format,
                Args.max_seconds,
                Args.native_ready,
            )
        else:
            Outcome = StartNewRun(Args, SourceRoot)
        if Args.codec_request and Outcome["status"] in {
            "completed",
            "coverage_incomplete",
        }:
            from CodecPatch import promote_scope

            Outcome["codec_patch"] = promote_scope(Args, Outcome)
        Output = canonical(
            {**Outcome, "result": str(Directory / "CatalogueResult.json")}
        )
        sys.stdout.buffer.write((Output + "\n").encode("utf-8"))
        return {
            "completed": 0,
            "coverage_incomplete": 2,
            "paused": 0,
            "failed": 1,
            "prepared": 0,
        }[Outcome["status"]]
    except Busy:
        Parser.exit(1, "catalogue run is already active\n")
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


# saved runs use the original inputs and runtime settings without making new claims
def CheckSavedArgs(Args):
    if (
        any(
            value is not None
            for value in (
                Args.catalogue,
                Args.solidworks_catalogue,
                Args.solidworks_sha256,
                Args.fusion_catalogue,
                Args.fusion_sha256,
                Args.workers,
                Args.reserved_memory_mib,
                Args.native_config,
                Args.native_kind,
                Args.native_resource,
                Args.advisor,
                Args.auth,
                Args.model,
                Args.advice_calls,
                Args.authoring_cases,
                Args.capture_mode,
                Args.authoring_grid,
                Args.solidworks_host,
                Args.fusion_lifecycle,
            )
        )
        or Args.author_samples
        or Args.prepare_only
        or Args.input is not None
        or Args.control
        or (Args.pause and (Args.native_ready or Args.max_seconds is not None))
    ):
        raise ValueError(
            "use the saved run directory without new input or worker options"
        )


# new batches turn explicit input options into a reusable prepared run
def StartNewRun(Args, SourceRoot):
    Reserve = (
        None
        if Args.reserved_memory_mib is None
        else bound_memory_reserve(Args.reserved_memory_mib)
    )
    Advice = read_options(Args)
    if Advice is not None and os.name != "posix":
        raise ValueError("decoder advice requires macOS or Linux")
    FileAudit = None
    if Args.batch_format == "auto" and not Args.input:
        raise ValueError("kit run auto requires --input")
    if Args.control and (
        not Args.input
        or (
            Args.batch_format != "auto"
            and (
                Args.batch_format != "solidworks"
                or Args.input.suffix.lower() != ".sldprt"
            )
        )
    ):
        raise ValueError("--control requires a SOLIDWORKS part --input")
    if Args.input:
        from InferenceGrid.FileScope import file_scope

        if not Args.batch_format or any(
            (
                Args.catalogue,
                Args.solidworks_catalogue,
                Args.fusion_catalogue,
                Args.fusion_sha256,
                Args.solidworks_sha256,
            )
        ):
            raise ValueError(
                "use --input with one kit run format and no catalogue options"
            )
        with TemporaryDirectory() as Scratch:
            Catalogues, FileAudit = file_scope(
                Args.input, Args.batch_format, Path(Scratch), SourceRoot, Args.control
            )
    else:
        Catalogues = ReadRunInputs(Args)
    Native = ReadNativeOptions(Args)
    if (
        Args.native_ready
        and Native is None
        and not (Args.author_samples and Args.solidworks_host is not None)
    ):
        raise ValueError("--native-ready requires the native worker configuration")
    Revision = git(SourceRoot, "rev-parse", "HEAD").decode("ascii").strip()
    if Args.author_samples:
        if Advice is not None:
            raise ValueError(
                "native sample authoring uses deterministic recipes without model advice"
            )
        from InferenceGrid.Authoring.RunAuthorBatch import RunAuthorBatch

        return RunAuthorBatch(
            Args.directory.resolve(),
            SourceRoot,
            Revision,
            Catalogues,
            bounded(1200 if Args.max_seconds is None else Args.max_seconds, 1, 86400),
            Native,
            CasePath=Args.authoring_cases,
            ModeValue=Args.capture_mode or "discovery",
            GridValue=Args.authoring_grid or "baseline",
            HostPath=Args.solidworks_host,
            Reserve=Reserve,
            LifecyclePath=Args.fusion_lifecycle,
            Workers=(
                4
                if Args.workers is None
                else bounded(Args.workers, 1, KMaxBatchWorkers)
            ),
            NativeReady=Args.native_ready,
            PrepareOnly=Args.prepare_only,
        )
    if (
        any(
            Value is not None
            for Value in (
                Args.authoring_cases,
                Args.capture_mode,
                Args.authoring_grid,
                Args.solidworks_host,
                Args.fusion_lifecycle,
            )
        )
        or Args.prepare_only
    ):
        raise ValueError("authoring options require --author-samples")
    return RunCatalogueBatch(
        Args.directory.resolve(),
        SourceRoot,
        Revision,
        Catalogues,
        bounded(1200 if Args.max_seconds is None else Args.max_seconds, 1, 86400),
        Native,
        Advice,
        Reserve=Reserve,
        Workers=KMaxBatchWorkers if Args.workers is None else Args.workers,
        NativeReady=Args.native_ready,
        FileScope=FileAudit,
        FileInput=Args.input,
    )


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
