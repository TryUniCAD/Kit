# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

from CodexAdvice.AdviceOptions import add_options


# automatic development is explicitly enabled and retains the existing model authorization options
def AddBuilderOptions(Parser):
    Parser.add_argument(
        "--auto-develop-builders",
        action="store_true",
        help="Generate repair and independently qualify a missing research builder",
    )
    Parser.add_argument("--builder-feature", default="family:planes:offset-plane")
    Parser.add_argument("--builder-api-metadata", type=Path)
    Parser.add_argument("--builder-registry", type=Path)
    Parser.add_argument("--builder-attempts", type=int, default=3)
    Parser.add_argument("--builder-model-calls", type=int, default=3)
    Parser.add_argument("--builder-call-seconds", type=int, default=180)
    Parser.add_argument("--builder-seconds", type=int, default=1800)
    Parser.add_argument("--builder-max-cost-usd", type=float)
    Parser.add_argument("--builder-demo-defect", action="store_true")
    Parser.add_argument("--builder-negative-probe", action="store_true")
    Parser.add_argument("--builder-resume", action="store_true")
    Parser.add_argument("--builder-pause", action="store_true")
    Parser.add_argument("--builder-extra-attempts", type=int, default=0)
    Parser.add_argument("--builder-extra-seconds", type=int, default=0)
    add_options(Parser)


# bounded extensions require explicit resumption and never silently reset the original budget
def CheckBuilderOptions(Parser, Args):
    if not Args.auto_develop_builders:
        if Args.advisor is not None or Args.builder_resume or Args.builder_pause:
            Parser.error("builder and model execution requires --auto-develop-builders")
        return
    if not 1 <= Args.builder_attempts <= 10 or not 1 <= Args.builder_model_calls <= 10:
        Parser.error("builder attempts and model calls must be between one and ten")
    if (
        not 1 <= Args.builder_call_seconds <= 3600
        or not 1 <= Args.builder_seconds <= 86400
    ):
        Parser.error("builder time limits exceed their supported bounds")
    if (
        not 0 <= Args.builder_extra_attempts <= 10
        or not 0 <= Args.builder_extra_seconds <= 86400
    ):
        Parser.error("invalid explicit builder budget extension")
    if (
        Args.builder_extra_attempts or Args.builder_extra_seconds
    ) and not Args.builder_resume:
        Parser.error("budget extensions require --builder-resume")
