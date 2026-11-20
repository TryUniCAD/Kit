# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from json import dumps, loads
from subprocess import DEVNULL, PIPE, run

from CodexAdvice.ProviderEnv import provider_env


# claude returns structured advice without access to the checkout or tools
def call_claude(executable, options, prompt, schema, work, seconds):
    process = run(
        [
            executable,
            "--print",
            "--safe-mode",
            "--tools",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--disallowedTools",
            "mcp__*",
            "--no-session-persistence",
            "--max-turns",
            "3",
            *(("--model", options.model) if options.model is not None else ()),
            "--output-format",
            "json",
            "--json-schema",
            dumps(schema),
        ],
        input=prompt,
        encoding="utf-8",
        cwd=work,
        stdout=PIPE,
        stderr=DEVNULL,
        timeout=seconds,
        env=provider_env(options),
        check=True,
    )
    try:
        result = loads(process.stdout)
        if result.get("is_error"):
            raise ValueError("Claude did not complete the advice request")
        return result["structured_output"]
    except (KeyError, AttributeError, ValueError):
        raise ValueError("Claude did not return a structured proposal") from None
