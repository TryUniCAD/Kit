# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from json import dumps, loads
from os import replace
from pathlib import Path
from tempfile import NamedTemporaryFile

from Records import digest
from InferenceGrid.RecipeCampaign.AssistPacket import AssistPacket


# durable snapshots let the assistant extend bindings without discarding completed attempts
def WriteState(PathValue, Value):
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=PathValue.parent,
        prefix="." + PathValue.name,
        delete=False,
    ) as Handle:
        Temporary = Path(Handle.name)
        Handle.write(dumps(Value, indent=2, sort_keys=True) + "\n")
    try:
        replace(Temporary, PathValue)
    finally:
        Temporary.unlink(missing_ok=True)


# input identities remain fixed while executable bindings may grow between steps
def MergePlan(Directory, PlanValue):
    StatePath = Directory / "Campaign.json"
    if StatePath.exists():
        State = loads(StatePath.read_text(encoding="utf-8"))
        if State["input_pins"] != PlanValue["input_pins"]:
            raise ValueError("campaign inputs changed; use a new campaign directory")
        for Key, Entry in PlanValue["entries"].items():
            Saved = State["entries"][Key]
            if Saved["row_sha256"] != Entry["row_sha256"]:
                raise ValueError("campaign recipe changed")
            for Field in ("binding", "mode", "needs_assistant"):
                Saved[Field] = Entry[Field]
            if Saved["status"] == "pending" or (
                Saved["status"] == "needs_assistant" and not Saved["attempts"]
            ):
                Saved["assistant_error"] = Entry["assistant_error"]
                Saved["status"] = (
                    "needs_assistant" if Entry["needs_assistant"] else "pending"
                )
        return State
    return {
        **PlanValue,
        "entries": {
            Key: {
                **Entry,
                "attempts": [],
                "native_verified": False,
                "status": "needs_assistant" if Entry["needs_assistant"] else "pending",
            }
            for Key, Entry in PlanValue["entries"].items()
        },
    }


# assistant statements can request another attempt but cannot manufacture native acceptance
def ReadReply(Directory, State):
    ReplyPath = Directory / "RecipeReply.json"
    if not ReplyPath.exists():
        return
    Reply = loads(ReplyPath.read_text(encoding="utf-8"))
    ReplyPin = digest(Reply)
    if State.get("last_reply_sha256") == ReplyPin:
        return
    if (
        set(Reply) != {"key", "recipe_sha256", "status", "reason"}
        or Reply["status"] not in {"ready", "skip"}
        or not isinstance(Reply["reason"], str)
        or not Reply["reason"].strip()
    ):
        raise ValueError("invalid assistant recipe reply")
    Entry = State["entries"].get(Reply["key"])
    if Entry is None or Entry["row_sha256"] != Reply["recipe_sha256"]:
        raise ValueError("assistant reply is for a different recipe")
    if Entry["status"] not in {"pending", "needs_assistant", "needs_host"}:
        raise ValueError("assistant reply cannot replace completed native evidence")
    Entry["assistant_reason"] = Reply["reason"]
    Entry["status"] = (
        "assistant_skipped"
        if Reply["status"] == "skip"
        else "needs_assistant" if Entry["needs_assistant"] else "pending"
    )
    if Reply["status"] == "ready" and Entry["needs_assistant"]:
        Entry["assistant_error"] = (
            "reply supplied no executable binding; implement the recipe mapping first"
        )
    State["last_reply_sha256"] = ReplyPin


# every waiting feature exposes its actual instructions rather than asking the operator to invent them
def WriteNext(Directory, State, SourceRoot):
    Waiting = [
        Entry
        for Entry in State["entries"].values()
        if Entry["status"] in {"needs_assistant", "needs_host"}
    ]
    PacketPath = Directory / "NextRecipe.json"
    if not Waiting:
        PacketPath.unlink(missing_ok=True)
        return None
    Entry = min(Waiting, key=lambda Value: (Value["application"], Value["recipe_id"]))
    Packet = AssistPacket(Entry, SourceRoot, Entry.get("assistant_error"))
    Packet["reply_path"] = str(Directory / "RecipeReply.json")
    Packet["previous_attempts"] = Entry["attempts"]
    WriteState(PacketPath, Packet)
    return Packet


# creation verification and decoding stay separate in the visible progress report
def Summarize(State):
    Counts = Counter(Entry["status"] for Entry in State["entries"].values())
    return {
        "schema_version": 1,
        "recipes": len(State["entries"]),
        "features": sum(len(Entry["aliases"]) for Entry in State["entries"].values()),
        "statuses": dict(sorted(Counts.items())),
        "native_verified_recipes": sum(
            Entry["native_verified"] for Entry in State["entries"].values()
        ),
        "features_without_written_recipe": sum(
            len(Items) for Items in State["unmapped"].values()
        ),
        "portable_complete": False,
    }
