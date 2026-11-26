# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot as KSourceRoot


# actual fixture and decoder processes need a shared schema and bounded runner registry
def BuildRegistry(TmpPath: FilePath) -> FilePath:
    SchemaPath = TmpPath / "ResultSchema.json"
    _ = SchemaPath.write_text('{"type":"object"}', encoding="utf-8")
    RegistryPath = TmpPath / "Registry.json"
    Registry = {
        "runners": {
            "fixture.capture.catalogue": {
                "pool": "fixture",
                "argv": [
                    PythonExe,
                    "-B",
                    str(FilePath(__file__).with_name("FixtureCapture.py")),
                    "{session}",
                ],
                "result_schema": str(SchemaPath),
                "initial_peak_memory_mib": 64,
                "max_memory_mib": 256,
            },
            "catalogue.decode": {
                "pool": "decode",
                "argv": [
                    PythonExe,
                    "-B",
                    str(
                        KSourceRoot
                        / "re/automation/InferenceGrid/Authoring/DecodeWorker.py"
                    ),
                    "{session}",
                ],
                "result_schema": str(SchemaPath),
                "initial_peak_memory_mib": 256,
                "max_memory_mib": 1024,
            },
        }
    }
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")
    return RegistryPath
