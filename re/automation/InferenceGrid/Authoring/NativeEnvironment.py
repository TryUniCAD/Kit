# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ
from pathlib import Path
from re import fullmatch

# native application configuration requires standard host paths without inheriting decoder credentials
KNativePaths = (
    "ALLUSERSPROFILE",
    "ProgramData",
    "APPDATA",
    "LOCALAPPDATA",
    "USERPROFILE",
    "PUBLIC",
    "ProgramFiles",
    "ProgramFiles(x86)",
    "ProgramW6432",
    "CommonProgramFiles",
    "CommonProgramFiles(x86)",
    "CommonProgramW6432",
    "SystemRoot",
    "WINDIR",
    "SystemDrive",
)


# callers cannot use native profile restoration to inject commands modules or secrets
def ValidateNative(Settings):
    if not isinstance(Settings, dict) or set(Settings) - set(KNativePaths):
        raise ValueError(
            "native environment accepts only reviewed Windows profile paths"
        )
    for NameValue, PathValue in Settings.items():
        if (
            not isinstance(PathValue, str)
            or not 1 <= len(PathValue) <= 4096
            or "\0" in PathValue
        ):
            raise ValueError("native environment path must be bounded text")
        if NameValue == "SystemDrive":
            if fullmatch("[A-Za-z]:", PathValue) is None:
                raise ValueError(
                    "native system drive must be a Windows drive identifier"
                )
        elif not Path(PathValue).is_absolute() or not Path(PathValue).is_dir():
            raise ValueError(
                "native environment must name existing absolute host directories"
            )
    return dict(Settings)


# trusted host preparation happens before the supervisor replaces its worker profile
def CaptureNative():
    return ValidateNative(
        {
            NameValue: environ[NameValue]
            for NameValue in KNativePaths
            if NameValue in environ
        }
    )
