# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys

from InferenceRunner import FIELD_KIND, GAP_KIND, RESCAN_KIND, result_schema
from Pilot.PilotFiles import WriteRecord


# an explicit deterministic registry prevents models or licensed application dispatch from entering this run
def PilotConfig(
    Directory, SourceRoot, Sessions, *, GroupRescans=True, GroupMaxMembers=20
):
    Schema = WriteRecord(Directory / "InferenceResult.json", result_schema())
    Entry = {
        "pool": "inference",
        "argv": [
            sys.executable,
            "-B",
            str(SourceRoot / "re/automation/InferenceRunner.py"),
            "{session}",
        ],
        "result_schema": str(Schema),
        "threads": 1,
        "initial_peak_memory_mib": 128,
        "max_memory_mib": 768,
    }
    Rescan = Entry
    if GroupRescans:
        Rescan = {
            **Entry,
            "group_protocol": 1,
            "group_limit_bytes": 16 * 1024 * 1024,
            "group_peak_memory_mib": 256,
        }
        if GroupMaxMembers != 20:
            Rescan["group_max_members"] = GroupMaxMembers
    Registry = WriteRecord(
        Directory / "Registry.json",
        {"runners": {FIELD_KIND: Entry, GAP_KIND: Entry, RESCAN_KIND: Rescan}},
    )
    Config = WriteRecord(
        Directory / "Supervisor.json",
        {
            "state": str(Directory / "State"),
            "controller": {"adapter": "a03", "store": str(Directory / "Store")},
            "registry": str(Registry),
            "worker": "supervisor:offline-pilot-a15a",
            "pools": {"inference": {"max_sessions": Sessions}},
            "reserved_cpus": 2,
            "reserved_memory_mib": 4096,
            "poll_seconds": 0.5,
            "stop_grace_seconds": 10,
        },
    )
    return Config, Registry, Schema
