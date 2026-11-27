# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import os
from queue import Empty, Full, Queue
from threading import Event, Thread
from time import monotonic

from InferenceGrid.BuilderDevelopment.Generation.Transport.CodexPolicy import (
    KOutputLimit,
)


# bounded threaded pipe reads work on both windows handles and posix descriptors
class SessionPipe:
    def __init__(self, Reader, Writer, Errors):
        self.reader, self.writer, self.errors = Reader, Writer, Errors
        self.queue = Queue(maxsize=64)
        self.stopped = Event()
        self.buffer = b""
        self.seen = 0
        self.write_threads = []
        self.thread = Thread(target=self._pump, daemon=True)
        self.thread.start()

    # backpressure bounds unread provider output without requiring platform specific pipe selectors
    def _pump(self):
        try:
            while not self.stopped.is_set():
                Raw = os.read(self.reader, 65536)
                Value = ("data", Raw) if Raw else ("eof", None)
                while not self.stopped.is_set():
                    try:
                        self.queue.put(Value, timeout=0.05)
                        break
                    except Full:
                        continue
                if not Raw:
                    return
        except OSError as Error:
            if not self.stopped.is_set():
                try:
                    self.queue.put(("error", str(Error)), timeout=0.05)
                except Full:
                    return

    # one call cannot hide excessive stderr behind an otherwise valid json result
    def _check(self, Deadline):
        if self.stopped.is_set():
            raise OSError("provider_closed: owned codex session was closed")
        self.errors.drain()
        if self.errors.seen > KOutputLimit or self.seen > KOutputLimit:
            raise OSError(
                "provider_output_limit: codex protocol output exceeded its bound"
            )
        if monotonic() >= Deadline:
            raise TimeoutError("provider_timeout: codex protocol deadline exceeded")

    # writing on a bounded helper thread allows a nonreading child to respect the request deadline
    def Send(self, Value, Deadline):
        self._check(Deadline)
        Raw = (
            json.dumps(Value, allow_nan=False, separators=(",", ":")) + "\n"
        ).encode()
        if len(Raw) > 256 * 1024:
            raise ValueError(
                "provider_input_limit: codex protocol request is too large"
            )
        Finished, Problems = Event(), []

        def WriteAll():
            try:
                Offset = 0
                while Offset < len(Raw) and not self.stopped.is_set():
                    Offset += os.write(self.writer, Raw[Offset:])
            except OSError as Error:
                Problems.append(Error)
            finally:
                Finished.set()

        Worker = Thread(target=WriteAll, daemon=True)
        self.write_threads.append(Worker)
        Worker.start()
        while not Finished.wait(0.05):
            self._check(Deadline)
        self._check(Deadline)
        Worker.join()
        self.write_threads.remove(Worker)
        if Problems:
            raise OSError(
                "provider_protocol_failed: codex request pipe failed"
            ) from Problems[0]

    # partial lines stay bounded and are decoded only when the complete json message arrives
    def Receive(self, Deadline):
        while True:
            self._check(Deadline)
            if b"\n" in self.buffer:
                Line, self.buffer = self.buffer.split(b"\n", 1)
                if not Line.strip():
                    continue
                try:
                    Value = json.loads(Line)
                except (UnicodeDecodeError, ValueError) as Error:
                    raise ValueError(
                        "provider_protocol_failed: malformed codex json"
                    ) from Error
                if not isinstance(Value, dict):
                    raise ValueError(
                        "provider_protocol_failed: codex message is not an object"
                    )
                return Value
            try:
                Kind, Value = self.queue.get(timeout=0.05)
            except Empty:
                continue
            if Kind != "data":
                raise OSError("provider_protocol_failed: codex protocol stream ended")
            self.seen += len(Value)
            self.buffer += Value

    # the owner first terminates the process tree so blocked pipe operations can finish safely
    def close(self):
        self.stopped.set()
        for Worker in tuple(self.write_threads):
            Worker.join(timeout=1)
        self.thread.join(timeout=1)
        for Descriptor in (self.reader, self.writer):
            try:
                os.close(Descriptor)
            except OSError:
                pass
