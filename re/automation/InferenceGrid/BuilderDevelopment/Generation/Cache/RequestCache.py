# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import dumps, loads
from os import link
from pathlib import Path
from sys import exc_info
from time import monotonic
from uuid import uuid4

from InferenceGrid.BuilderDevelopment.Generation.Cache.RequestLock import HoldRequest
from InferenceGrid.BuilderDevelopment.Generation.GenerationPaths import (
    CheckComponents,
    OwnedPath,
)
from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ValidateProgram
from Records import digest


# cache identity includes generation policy so changed code cannot inherit stale model choices
def GenerationPin():
    Root = CheckComponents(Path(__file__).absolute()).parents[1]
    for Entry in Root.rglob("*"):
        CheckComponents(Entry)
    return digest(
        [
            [
                Source.relative_to(Root).as_posix(),
                sha256(CheckComponents(Source).read_bytes()).hexdigest(),
            ]
            for Source in sorted(Root.rglob("*.py"))
        ]
    )


# only identical authorized requests share candidates and qualification remains independently required
class RequestCache:
    def __init__(self, Budget, PacketPin, Options, Schema):
        self.enabled = (
            Options.provider == "codex"
            and Options.auth == "login"
            and Options.model is not None
        )
        self.lock = None
        self.wait_seconds = 0.0
        self.record = None
        if not self.enabled:
            return
        from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexIdentity import (
            CodexIdentity,
        )

        Root = CheckComponents(
            Budget.get("shared_root", Path(Budget["run_root"]) / "GenerationCache")
        )
        SourceRoot = Path(__file__).resolve().parents[6]
        if Root.is_relative_to(SourceRoot):
            raise ValueError("generation cache must remain outside the source checkout")
        Root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.root = OwnedPath(Root, Root)
        self.options = Options
        self.source_pin = GenerationPin()
        self.provider_pin = CodexIdentity(Options)
        self.key = digest(
            {
                "packet_sha256": PacketPin,
                "provider": Options.provider,
                "auth": Options.auth,
                "model": Options.model,
                "schema": Schema,
                "generation_sources": self.source_pin,
                "provider_identity": self.provider_pin,
                "personal_instructions": Budget.get("personal_instructions", False),
            }
        )
        self.path = OwnedPath(self.root / (self.key + ".json"), self.root)
        self.lock = HoldRequest(
            OwnedPath(self.root / (self.key + ".lock"), self.root),
            Budget["max_seconds"],
        )

    # process released ownership covers model accounting and publication rather than only cache reads
    def __enter__(self):
        if self.lock is not None:
            Started = monotonic()
            self.lock.__enter__()
            self.wait_seconds = monotonic() - Started
            try:
                self.record = self.Read()
            except BaseException:
                self.lock.__exit__(*exc_info())
                raise
        return self

    # closing a request never leaves an advisory lock behind after interruption or an exception
    def __exit__(self, *Details):
        if self.lock is not None:
            return self.lock.__exit__(*Details)

    # invalid or truncated runtime records are retained without being treated as accepted candidates
    def Read(self):
        if not self.path.exists():
            return None
        try:
            if not self.path.is_file() or self.path.stat().st_size > 65536:
                raise ValueError("invalid record size or type")
            Entry = loads(OwnedPath(self.path, self.root).read_text(encoding="utf-8"))
            if not isinstance(Entry, dict):
                raise ValueError("record is not an object")
            if Entry.get("schema_version") != 1 or Entry.get("key") != self.key:
                raise ValueError("record identity differs from the request")
            if Entry.get("sha256") != digest(
                {Key: Value for Key, Value in Entry.items() if Key != "sha256"}
            ):
                raise ValueError("record integrity failed")
            Entry["program"] = ValidateProgram(Entry["program"])
            return Entry
        except (OSError, ValueError, KeyError, TypeError) as Error:
            raise ValueError(
                "generation_cache_invalid: existing record was retained without another model call"
            ) from Error

    # reuse records zero new provider usage while retaining the original generation provenance
    def Hit(self):
        if self.record is None:
            return None
        return {
            "status": "candidate",
            "classification": "candidate_reused",
            "program": self.record["program"],
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_input_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0,
                "accounting": "reused",
            },
            "cache": {
                "hit": True,
                "key": self.key,
                "record_sha256": self.record["sha256"],
                "original_usage": self.record["usage"],
                "wait_seconds": self.wait_seconds,
            },
            "native_verified": False,
        }

    # an immutable candidate is published only after the original provider reservation was finalized
    def Store(self, Result, PacketPin, PromptPin):
        if (
            not self.enabled
            or Result.get("status") != "candidate"
            or self.path.exists()
        ):
            return
        from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexIdentity import (
            CodexIdentity,
        )

        if (
            GenerationPin() != self.source_pin
            or CodexIdentity(self.options) != self.provider_pin
        ):
            raise ValueError(
                "provider_context_changed: generation context changed before cache publication"
            )
        Entry = {
            "schema_version": 1,
            "key": self.key,
            "packet_sha256": PacketPin,
            "prompt_sha256": PromptPin,
            "program": ValidateProgram(Result["program"]),
            "usage": Result["usage"],
            "native_verified": False,
            "conversion_qualified": False,
        }
        Entry["sha256"] = digest(Entry)
        Temporary = OwnedPath(
            self.root / (self.key + "." + uuid4().hex + ".tmp"), self.root
        )
        try:
            with Temporary.open("x", encoding="utf-8") as Output:
                Output.write(
                    dumps(Entry, indent=2, sort_keys=True, allow_nan=False) + "\n"
                )
            try:
                link(Temporary, self.path)
            except FileExistsError:
                pass
        finally:
            Temporary.unlink(missing_ok=True)
