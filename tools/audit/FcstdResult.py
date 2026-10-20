# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from pathlib import Path as FilePath
from typing import Any as AnyValue

from tools.audit.FcstdContext import KRepositoryRoot


# stable path rendering keeps audit records portable inside and outside the repository
def GetDisplayPath(SourcePath: FilePath) -> str:
    if SourcePath.is_relative_to(KRepositoryRoot):
        return str(SourcePath.relative_to(KRepositoryRoot))
    return str(SourcePath)


# unsupported records distinguish missing native grammar from parser or writer failures
def MakeUnsupported(
    SourcePath: FilePath, TypeNames: tuple[str, ...]
) -> dict[str, AnyValue]:
    return {
        "path": GetDisplayPath(SourcePath),
        "kind": "part",
        "feature_types": TypeNames,
        "application_usable": False,
        "vendor_loadable": False,
        "near_lossless": False,
        "native_capabilities": (),
        "requirements": ("no_typed_native_feature_program",),
        "bytes": 0,
        "streams": 0,
        "error": "",
    }


# failure records preserve batch progress because one malformed source must not hide others
def MakeFailure(SourcePath: FilePath, ErrorText: str) -> dict[str, AnyValue]:
    return {
        "path": GetDisplayPath(SourcePath),
        "kind": "unknown",
        "feature_types": (),
        "application_usable": False,
        "vendor_loadable": False,
        "near_lossless": False,
        "native_capabilities": (),
        "requirements": (),
        "bytes": 0,
        "streams": 0,
        "error": ErrorText,
    }
