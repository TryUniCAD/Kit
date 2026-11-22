# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ

from InferenceGrid.Authoring.NativeEnvironment import CaptureNative, ValidateNative

# native children retain task scratch paths while inheriting no arbitrary caller credentials
KInheritKeys = (
    "PATH",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TZ",
    "HOME",
    "TMPDIR",
    "KIT_SESSION",
    "SystemRoot",
    "WINDIR",
    "PATHEXT",
    "USERPROFILE",
    "TEMP",
    "TMP",
)


# only the native application receives its explicitly prepared host profile directories
def NativeSolidEnv(HostConfig):
    NativeValues = (
        CaptureNative()
        if "native_environment" not in HostConfig
        else ValidateNative(HostConfig["native_environment"])
    )
    Environment = {Name: environ[Name] for Name in KInheritKeys if Name in environ}
    Environment.update(NativeValues)
    return Environment
