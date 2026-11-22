# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import loads
from os import environ
from pathlib import Path
from shutil import which


# bounded local hashes invalidate candidate reuse without reading credentials or starting a model session
def FilePin(Value, Limit):
    Target = Path(Value).resolve()
    if not Target.exists():
        return {"path": str(Target), "present": False}
    Before = Target.stat()
    if not Target.is_file() or Before.st_size > Limit:
        raise ValueError(
            "provider_context_limit: codex identity file exceeds its bound"
        )
    Hash, Count = sha256(), 0
    with Target.open("rb") as Source:
        while Chunk := Source.read(65536):
            Count += len(Chunk)
            if Count > Limit:
                raise ValueError(
                    "provider_context_limit: codex identity file grew beyond its bound"
                )
            Hash.update(Chunk)
    After = Target.stat()
    if (Before.st_dev, Before.st_ino, Before.st_size, Before.st_mtime_ns) != (
        After.st_dev,
        After.st_ino,
        After.st_size,
        After.st_mtime_ns,
    ):
        raise ValueError(
            "provider_context_changed: codex identity file changed while hashing"
        )
    return {
        "path": str(Target),
        "present": True,
        "sha256": Hash.hexdigest(),
        "size_bytes": Count,
    }


# model routing and personal instruction changes must not reuse an unrelated unqualified candidate
def CodexIdentity(Options):
    if Options.provider != "codex" or Options.auth != "login":
        raise ValueError(
            "provider_unavailable: persistent identity requires codex login"
        )
    Executable = which("codex")
    if Executable is None:
        raise ValueError("provider_unavailable: codex CLI is not installed")
    Resolved = Path(Executable).resolve()
    CodexHome = Path(environ.get("CODEX_HOME", Path.home() / ".codex")).resolve()
    Identity = {
        "provider": Options.provider,
        "auth": Options.auth,
        "model": Options.model,
        "executable": FilePin(Resolved, 512 * 1024 * 1024),
        "global_instructions": [
            FilePin(CodexHome / Name, 512 * 1024)
            for Name in ("AGENTS.md", "AGENTS.override.md")
        ],
        "version": None,
    }
    Package = Resolved.parent.parent / "package.json"
    if Resolved.suffix in (".js", ".mjs", ".cjs") and Package.is_file():
        Identity["package"] = FilePin(Package, 64 * 1024)
        Metadata = loads(Package.read_text(encoding="utf-8"))
        Version = Metadata.get("version")
        if isinstance(Version, str) and len(Version) <= 128:
            Identity["version"] = Version
    return Identity
