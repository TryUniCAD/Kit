# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import os
from threading import Lock

from CodexAdvice.ProviderEnv import provider_env
from InferenceGrid.BuilderDevelopment.Generation.OwnedProviderProcess import (
    OwnedProviderProcess,
)
from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexPolicy import (
    KOutputLimit,
)
from InferenceGrid.BuilderDevelopment.Generation.Transport.SessionPipe import (
    SessionPipe,
)
from LogCapture import LogCapture


# one owned job or process group contains the persistent server and all of its descendants
class SessionProcess:
    def __init__(self, Command, Options, Directory):
        self.owner, self.pipe, self.errors = None, None, None
        self.closed = False
        self.cleanup_error = None
        self.close_lock = Lock()
        InputReader, InputWriter = os.pipe()
        OutputReader, OutputWriter = os.pipe()
        try:
            self.errors = LogCapture(Directory / "Server.stderr", KOutputLimit)
            self.owner = OwnedProviderProcess(
                Command,
                Directory,
                provider_env(Options),
                OutputWriter,
                self.errors.writer,
                InputReader,
            )
            self.errors.close_writer()
            self.pipe = SessionPipe(OutputReader, InputWriter, self.errors)
        except BaseException:
            for Descriptor in (OutputReader, InputWriter):
                try:
                    os.close(Descriptor)
                except OSError:
                    pass
            self.close()
            raise
        finally:
            os.close(InputReader)
            os.close(OutputWriter)

    # concurrent controller shutdown and request failure must perform owned cleanup exactly once
    def close(self):
        with self.close_lock:
            if self.closed:
                if self.cleanup_error is not None:
                    raise self.cleanup_error
                return
            self.closed = True
            try:
                if self.owner is not None:
                    self.owner.close()
            except OSError as Error:
                self.cleanup_error = OSError(
                    "provider_cleanup_failed: owned codex server cleanup failed"
                )
                raise self.cleanup_error from Error
            finally:
                if self.pipe is not None:
                    self.pipe.close()
                if self.errors is not None:
                    self.errors.close()
