# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import unlink as UnlinkFile
from pathlib import Path as FilePath
from stat import FILE_ATTRIBUTE_REPARSE_POINT as KReparseFlag
from stat import S_ISREG as IsRegular
from stat import S_IWUSR as KWriteMode
from types import TracebackType


# git stores immutable objects readonly so owned clone teardown needs a bounded retry
def RetryReadonly(
    OwnerRoot: FilePath,
    Action: object,
    TargetName: str,
    ErrorInfo: tuple[type[BaseException], BaseException, TracebackType],
) -> None:
    Failure = ErrorInfo[1]
    if not isinstance(Failure, PermissionError) or Action is not UnlinkFile:
        raise Failure
    TargetPath = FilePath(TargetName)
    FileInfo = TargetPath.lstat()
    if (
        not IsRegular(FileInfo.st_mode)
        or FileInfo.st_mode & KWriteMode
        or FileInfo.st_nlink != 1
        or getattr(FileInfo, "st_file_attributes", 0) & KReparseFlag
        or not TargetPath.resolve(strict=True).is_relative_to(OwnerRoot)
    ):
        raise Failure
    TargetPath.chmod(FileInfo.st_mode | KWriteMode)
    UnlinkFile(TargetPath)
