# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import os
import signal
import subprocess
import sys
from time import monotonic, sleep

from LogCapture import LogCapture


# a held Windows job or unreaped POSIX process leader owns every provider descendant
class OwnedProviderProcess:
    def __init__(self, Command, Directory, Environment, Stdout, Stderr, Stdin):
        self.windows = sys.platform == "win32"
        if self.windows:
            from WindowsProcess import WindowsProcess

            self.process = WindowsProcess(
                Command, Directory, Environment, Stdout, Stderr, stdin=Stdin
            )
        else:
            self.process = subprocess.Popen(
                Command,
                cwd=Directory,
                env=Environment,
                stdin=Stdin,
                stdout=Stdout,
                stderr=Stderr,
                start_new_session=True,
                close_fds=True,
            )

    # POSIX WNOWAIT keeps the group leader identity reserved until descendants are terminated
    def poll(self):
        if self.windows:
            return self.process.poll()
        Status = os.waitid(
            os.P_PID, self.process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT
        )
        if Status is None:
            return None
        return (
            Status.si_status if Status.si_code == os.CLD_EXITED else -Status.si_status
        )

    # every completion path stops remaining descendants and verifies the owned tree is no longer running
    def close(self):
        if self.windows:
            try:
                self.process.signal(9)
                self.process.wait(timeout=5)
                self.process.finish()
            finally:
                self.process.close()
            return
        from Processes import group_running

        try:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            Deadline = monotonic() + 5
            while group_running(self.process.pid):
                if monotonic() >= Deadline:
                    raise OSError(
                        "provider_cleanup_failed: owned POSIX descendants did not terminate"
                    )
                sleep(0.01)
        finally:
            self.process.wait(timeout=5)


# stdout retention is capped while the provider is alive rather than after an unbounded disk write
def RunProvider(Command, Directory, Environment, Seconds, Limit=4 * 1024 * 1024):
    Capture = LogCapture(Directory / "Provider.jsonl", Limit)
    Process, Code, Reason = None, None, None
    try:
        with (Directory / "Prompt.txt").open("rb") as Input, open(
            os.devnull, "wb"
        ) as Errors:
            Process = OwnedProviderProcess(
                Command,
                Directory,
                Environment,
                Capture.writer,
                Errors.fileno(),
                Input.fileno(),
            )
        Capture.close_writer()
        Deadline = monotonic() + Seconds
        while True:
            Capture.drain()
            if Capture.seen > Limit:
                Reason = "provider_output_limit"
                break
            Code = Process.poll()
            if Code is not None:
                break
            if monotonic() >= Deadline:
                Reason = "provider_timeout"
                break
            sleep(0.01)
    finally:
        try:
            if Process is not None:
                Process.close()
        finally:
            Capture.close()
    Receipt = Capture.receipt()
    if Receipt["dropped_bytes"]:
        Reason = "provider_output_limit"
    return {
        "returncode": Code,
        "stop_reason": Reason,
        "capture": Receipt,
        "owned_tree_termination_verified": True,
    }
