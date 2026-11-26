# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from Pilot.PilotFiles import WriteRecord
from Records import read_record
from Supervisor import ROOT, read_config
from Runners import Registry


# preserve native install paths when composing the registries into a private run
def MergeRunners(Offline, Native):
    LocalRunners = read_record(Offline)["runners"]
    NativeRunners = read_record(Native)["runners"]
    for KindName, Entry in NativeRunners.items():
        if KindName in LocalRunners:
            continue
        if Entry["pool"] == "inference":
            raise ValueError("reserve the inference pool for catalogue decoder jobs")
        if "application_installation" in Entry:
            Entry = {
                **Entry,
                "application_installation": str(
                    (Native.parent / Entry["application_installation"]).resolve()
                ),
            }
        LocalRunners[KindName] = Entry
    return LocalRunners


# one supervisor budgets the decoder and native pools against the same host
def BuildWorkerCfg(Directory, OfflinePath, NativePath, KindName, Resource):
    Offline = read_config(OfflinePath)
    Native = read_config(NativePath)
    if Offline["controller"] != Native["controller"]:
        raise ValueError("native supervisor must use this run's private A03 store")
    if Native["resources"].get(Resource) != 1:
        raise ValueError("select a configured capacity-one native resource")
    NativeRegistry = Registry(Native["registry"], ROOT)
    if KindName not in NativeRegistry.runners:
        raise ValueError("native job kind must be registered")
    Runners = MergeRunners(Offline["registry"], Native["registry"])
    if KindName not in Runners or Runners[KindName]["pool"] == "inference":
        raise ValueError("native worker requires its own pool")
    UsedPools = {Entry["pool"] for Entry in Runners.values()}
    Pools = {
        Name: Settings
        for Name, Settings in {**Native["pools"], **Offline["pools"]}.items()
        if Name in UsedPools
    }
    if set(Pools) != UsedPools:
        raise ValueError("every pipeline worker requires a configured pool")
    RegistryPath = WriteRecord(
        Directory / "PipelineRegistry.json", {"runners": Runners}
    )
    return WriteRecord(
        Directory / "PipelineSupervisor.json",
        {
            **read_record(NativePath),
            "state": str(Offline["state"]),
            "controller": Offline["controller"],
            "registry": str(RegistryPath),
            "pools": Pools,
            "reserved_memory_mib": Native["reserved_memory_mib"],
            "reserved_cpus": Native["reserved_cpus"],
        },
    )
