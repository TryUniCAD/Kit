# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from os import getpid as ProcessId
from pathlib import Path as FilePath
from sys import argv as CliArgs, stdin as InputStream
from tests.Research.Inference.BuilderDevelopment.Transport.FixtureChild import (
    StartChild,
)
from tests.Research.Inference.BuilderDevelopment.Transport.FixtureReply import SendReply
from tests.Research.Inference.BuilderDevelopment.Transport.FixtureThread import (
    ThreadReply,
)
from tests.Research.Inference.BuilderDevelopment.Transport.FixtureTurn import SendTurn


# an independent process implements the documented protocol without simulating model or native qualification
def MainServer() -> None:
    ModeName, LogPath = CliArgs[1], FilePath(CliArgs[2])
    ThreadCount = 0
    ThreadId = ""
    for RawLine in InputStream:
        Request = DecodeJson(RawLine)
        with LogPath.open("a", encoding="utf-8") as LogFile:
            _ = LogFile.write(
                EncodeJson({"pid": ProcessId(), "request": Request}) + "\n"
            )
        Method = Request.get("method")
        if Method == "initialize":
            if ModeName == "descendant":
                StartChild(LogPath)
            Reply = {"userAgent": "fixture"}
        elif Method == "model/list":
            Reply = {
                "data": [
                    {"id": Model, "model": Model}
                    for Model in ("gpt-6.1-terra", "gpt-6.1-sol")
                ],
                "nextCursor": None,
            }
        elif Method == "thread/start":
            ThreadCount += 1
            ThreadId = f"fixture-thread-{ThreadCount}"
            Reply = ThreadReply(Request["params"], ModeName, ThreadId)
        elif Method == "turn/start":
            SendTurn(Request, ModeName, ThreadId, ThreadCount)
            continue
        elif Method == "thread/unsubscribe":
            Reply = {"status": "unloaded"}
        else:
            continue
        SendReply({"id": Request["id"], "result": Reply})


if __name__ == "__main__":
    MainServer()
