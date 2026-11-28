# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import contextmanager
from errno import EACCES, EAGAIN, EDEADLK
from os import O_CREAT, O_RDWR, close, open as OpenFile
from sys import platform
from time import monotonic, sleep

from InferenceGrid.BuilderDevelopment.Generation.GenerationPaths import CheckComponents


# identical requests wait for an existing owner instead of spending another provider call
@contextmanager
def HoldRequest(PathValue, Seconds):
    Target = CheckComponents(PathValue)
    Descriptor = OpenFile(Target, O_CREAT | O_RDWR, 0o600)
    Deadline = monotonic() + Seconds
    try:
        while True:
            try:
                if platform == "win32":
                    import msvcrt

                    msvcrt.locking(Descriptor, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(Descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as Error:
                if Error.errno not in {EACCES, EAGAIN, EDEADLK}:
                    raise
                if monotonic() >= Deadline:
                    raise TimeoutError(
                        "provider_timeout: waiting for an identical generation request"
                    ) from Error
                sleep(min(0.05, max(0, Deadline - monotonic())))
        yield
    finally:
        close(Descriptor)
