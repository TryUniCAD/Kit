# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from sys import executable

from InferenceGrid.CatalogueWorkerConfig import BuildWorkerCfg
from InferenceGrid.Authoring.NativeEnvironment import CaptureNative, ValidateNative
from InferenceGrid.Authoring.AddSolidRunners import AddSolidRunners
from Pilot.PilotConfig import PilotConfig
from Pilot.PilotFiles import WriteRecord
from Records import read_record
from Sessions import write_private
from Supervisor import read_config


# a catalogue decoder records actual reader evidence without asserting native conversion acceptance
def AddDecode(Directory, SourceRoot, ConfigPath):
    ConfigValue = read_record(ConfigPath)
    RegistryPath = Path(ConfigValue["registry"])
    RegistryValue = read_record(RegistryPath)
    SchemaPath = WriteRecord(Directory / "AuthorResultSchema.json", {"type": "object"})
    RegistryValue["runners"]["catalogue.decode"] = {
        "pool": "inference",
        "argv": [
            executable,
            "-B",
            str(SourceRoot / "re/automation/InferenceGrid/Authoring/DecodeWorker.py"),
            "{session}",
        ],
        "result_schema": str(SchemaPath),
        "threads": 1,
        "initial_peak_memory_mib": 256,
        "max_memory_mib": 1024,
    }
    write_private(RegistryPath, RegistryValue)
    return ConfigValue, SchemaPath


# application dispatch stays isolated from reader pools and retains capacity one ownership
def AuthorConfig(Directory, SourceRoot, Workers, Native, HostPath):
    ConfigPath, _, _ = PilotConfig(Directory, SourceRoot, Workers)
    ConfigValue, SchemaPath = AddDecode(Directory, SourceRoot, ConfigPath)
    Resources = {}
    if HostPath is not None:
        HostValue = read_record(HostPath)
        if not {"interop_assembly", "executable"} <= set(HostValue) or set(
            HostValue
        ) - {"interop_assembly", "executable", "phase_seconds", "native_environment"}:
            raise ValueError("SOLIDWORKS host requires interop_assembly and executable")
        for NameValue in ("interop_assembly", "executable"):
            FileValue = Path(HostValue[NameValue])
            if not FileValue.is_absolute() or not FileValue.is_file():
                raise ValueError(
                    "SOLIDWORKS host paths must be absolute installed files"
                )
        HostValue["native_environment"] = (
            ValidateNative(HostValue["native_environment"])
            if "native_environment" in HostValue
            else CaptureNative()
        )
        HostFile = WriteRecord(Directory / "SolidWorksHost.json", HostValue)
        AddSolidRunners(ConfigValue, SourceRoot, SchemaPath, HostFile)
        Resources["solidworks"] = "application:solidworks:catalogue"
        ConfigValue["pools"]["authoring-solidworks"] = {"max_sessions": 1}
        ConfigValue["resources"] = {Resources["solidworks"]: 1}
        write_private(ConfigPath, ConfigValue)
    if Native is not None:
        NativePath, KindValue, ResourceValue = Native
        NativeValue = read_config(NativePath)
        Prepared = {
            **read_record(NativePath),
            "registry": str(NativeValue["registry"]),
            "state": str(Directory / "NativeState"),
            "controller": ConfigValue["controller"],
            "resources": {
                **NativeValue["resources"],
                **ConfigValue.get("resources", {}),
            },
        }
        NativeCopy = WriteRecord(Directory / "NativeSupervisor.json", Prepared)
        ConfigPath = BuildWorkerCfg(
            Directory, ConfigPath, NativeCopy, KindValue, ResourceValue
        )
        Resources["fusion"] = ResourceValue
    return ConfigPath, Resources
