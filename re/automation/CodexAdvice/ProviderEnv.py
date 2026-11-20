# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


import os


# only the requested cloud provider receives its explicit key override
def provider_env(options):
    env = os.environ.copy()
    overrides = {
        key: env.pop(key, None)
        for key in (
            "CODEX_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "OPENAI_BASE_URL",
            "ANTHROPIC_BASE_URL",
            "CLAUDE_CODE_USE_BEDROCK",
            "CLAUDE_CODE_USE_VERTEX",
            "CLAUDE_CODE_USE_FOUNDRY",
            "CLAUDE_CODE_USE_GATEWAY",
        )
    }
    if options.auth == "api":
        if options.provider == "codex":
            env["CODEX_API_KEY"] = (
                overrides["CODEX_API_KEY"] or overrides["OPENAI_API_KEY"]
            )
        else:
            env["ANTHROPIC_API_KEY"] = overrides["ANTHROPIC_API_KEY"]
    return env
