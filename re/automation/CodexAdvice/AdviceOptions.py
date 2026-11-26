# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass
import os
import re
from shutil import which
from pathlib import Path

from Records import bounded


# explicit modes keep credential selection separate from provider selection
@dataclass(frozen=True)
class AdviceOptions:
    provider: str
    auth: str
    model: str | None
    calls: int
    state: str | None = None
    global_calls: int = 16
    parallel: int = 1

    def arguments(self):
        return [
            "--advisor",
            self.provider,
            "--auth",
            self.auth,
            *(("--model", self.model) if self.model is not None else ()),
            "--advice-calls",
            str(self.calls),
            *(
                (
                    "--advice-state",
                    self.state,
                    "--advice-global-calls",
                    str(self.global_calls),
                    "--advice-parallel",
                    str(self.parallel),
                )
                if self.state is not None
                else ()
            ),
        ]


# both command entry points accept identical advice settings
def add_options(parser):
    parser.add_argument("--advisor", choices=("codex", "claude", "ollama"))
    parser.add_argument(
        "--auth",
        choices=("login", "api", "local"),
        help="Use CLI sign in, an API key, or a model on this machine",
    )
    parser.add_argument("--model", help="Model ID or local Ollama tag")
    parser.add_argument(
        "--advice-calls",
        type=int,
        metavar="N",
        help="Maximum advice calls during this run (default: 4)",
    )

    parser.add_argument(
        "--advice-state",
        type=Path,
        help="Owner-private local directory shared by AI advice runs",
    )
    parser.add_argument(
        "--advice-global-calls",
        type=int,
        metavar="N",
        help="Fixed cumulative calls per shared provider (default: 16)",
    )
    parser.add_argument(
        "--advice-parallel",
        type=int,
        metavar="N",
        help="Fixed concurrent calls per shared provider (default: 1)",
    )


# validate configuration before creating batch state or submitting jobs
def read_options(args):
    shared_state = getattr(args, "advice_state", None)
    shared_calls = getattr(args, "advice_global_calls", None)
    shared_parallel = getattr(args, "advice_parallel", None)
    if args.advisor is None:
        if any(
            value is not None
            for value in (
                args.auth,
                args.model,
                args.advice_calls,
                shared_state,
                shared_calls,
                shared_parallel,
            )
        ):
            raise ValueError("advice options require --advisor")
        return None
    if shared_state is None and any(
        value is not None for value in (shared_calls, shared_parallel)
    ):
        raise ValueError("shared advice limits require --advice-state")
    global_calls = bounded(16 if shared_calls is None else shared_calls, 1, 10000)
    parallel = bounded(1 if shared_parallel is None else shared_parallel, 1, 16)
    provider = args.advisor
    auth = args.auth or ("local" if provider == "ollama" else "login")
    if (auth == "local") != (provider == "ollama"):
        raise ValueError("local model inference requires --advisor ollama --auth local")
    model = args.model
    if model is None and provider == "codex":
        model = "gpt-6.2-sol"
    if model is not None and not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", model
    ):
        raise ValueError("specify a valid --model ID or local model tag")
    if provider == "ollama":
        if model is None:
            raise ValueError("--advisor ollama requires an installed --model")
        if model.casefold().endswith(("-cloud", ":cloud")):
            raise ValueError(
                "select an installed local model rather than an Ollama cloud tag"
            )
    if shared_state is not None and model is None:
        raise ValueError("shared advice requires an explicit --model")
    if provider != "ollama" and which(provider) is None:
        raise ValueError(f"install the {provider} CLI and add it to PATH")
    if auth == "api":
        keys = (
            ("CODEX_API_KEY", "OPENAI_API_KEY")
            if provider == "codex"
            else ("ANTHROPIC_API_KEY",)
        )
        if not any(os.environ.get(key) for key in keys):
            raise ValueError(f"set {' or '.join(keys)} for {provider} API mode")
    return AdviceOptions(
        provider,
        auth,
        model,
        bounded(4 if args.advice_calls is None else args.advice_calls, 1, 256),
        str(shared_state.absolute()) if shared_state is not None else None,
        global_calls,
        parallel,
    )
