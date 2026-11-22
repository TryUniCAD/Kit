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

from Records import bounded


# explicit modes keep credential selection separate from provider selection
@dataclass(frozen=True)
class AdviceOptions:
    provider: str
    auth: str
    model: str | None
    calls: int

    def arguments(self):
        return [
            "--advisor",
            self.provider,
            "--auth",
            self.auth,
            *(("--model", self.model) if self.model is not None else ()),
            "--advice-calls",
            str(self.calls),
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


# validate configuration before creating batch state or submitting jobs
def read_options(args):
    if args.advisor is None:
        if any(
            value is not None for value in (args.auth, args.model, args.advice_calls)
        ):
            raise ValueError("--auth, --model and --advice-calls require --advisor")
        return None
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
    )
