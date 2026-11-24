# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from re import fullmatch

from InferenceGrid.Authoring.NativeEnvironment import ValidateNative


# only a saved catalogue configuration may authorize native workers to share a campaign
def ValidateSolidHost(Host, *, Prepared):
    Expected = {"interop_assembly", "executable"}
    Optional = {"phase_seconds", "native_environment", "capture_workers"}
    if Prepared:
        Optional.add("parallel_group")
    if (
        not isinstance(Host, dict)
        or not Expected <= Host.keys()
        or Host.keys() - (Expected | Optional)
    ):
        raise ValueError("SOLIDWORKS host requires executable and interop paths")
    for Key in sorted(Expected):
        Value = Host[Key]
        if not isinstance(Value, str) or not Path(Value).is_absolute() or not Path(Value).is_file():
            raise ValueError("SOLIDWORKS host paths must name existing absolute files")
    Timeout = Host.get("phase_seconds", 600)
    if type(Timeout) is not int or not 1 <= Timeout <= 86400:
        raise ValueError("SOLIDWORKS phase timeout must be between 1 and 86400 seconds")
    Workers = Host.get("capture_workers", 1)
    if type(Workers) is not int or Workers not in (1, 2):
        raise ValueError("SOLIDWORKS capture_workers must be 1 or 2")
    if Prepared:
        Group = Host.get("parallel_group")
        if Workers == 2:
            if not isinstance(Group, str) or fullmatch("[0-9a-f]{32}", Group) is None:
                raise ValueError("parallel SOLIDWORKS workers require their prepared catalogue group")
        elif "parallel_group" in Host:
            raise ValueError("a single SOLIDWORKS worker cannot join a parallel group")
    if "native_environment" in Host:
        ValidateNative(Host["native_environment"])
    return Workers
