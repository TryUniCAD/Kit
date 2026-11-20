# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from sys import executable

from Records import read_record
from Sessions import write_private


# legacy captures and bounded native batches must share the same serialized host resource and isolation
def AddSolidRunners(ConfigValue, SourceRoot, SchemaPath, HostFile):
    RegistryPath = Path(ConfigValue["registry"])
    RegistryValue = read_record(RegistryPath)
    for KindValue, ScriptName in (
        ("capture.catalogue.solidworks", "SolidWorker.py"),
        ("capture.catalogue.solidworks.batch", "SolidBatchWorker.py"),
    ):
        RegistryValue["runners"][KindValue] = {
            "pool": "authoring-solidworks",
            "argv": [
                executable,
                "-B",
                str(SourceRoot / "re/automation/InferenceGrid/Authoring" / ScriptName),
                "--host",
                str(HostFile),
                "{session}",
            ],
            "result_schema": str(SchemaPath),
            "initial_peak_memory_mib": 2048,
            "max_memory_mib": 8192,
        }
    write_private(RegistryPath, RegistryValue)
