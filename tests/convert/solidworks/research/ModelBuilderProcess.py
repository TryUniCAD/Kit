from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

KRepoRoot = FilePath(__file__).resolve().parents[4]

KImports = """
from json import dumps as EncodeJson
import sys as SystemLib
from pathlib import Path as FilePath

WorkRoot = FilePath(SystemLib.argv[1])
CountCfg = int(SystemLib.argv[2])
DensityVal = float(SystemLib.argv[3])
NamePrefix = SystemLib.argv[4]
SystemLib.dont_write_bytecode = True
SystemLib.path.insert(0, str(WorkRoot))
SystemLib.path.insert(0, str(WorkRoot / "src"))
SystemLib.path.insert(0, str(WorkRoot / "re" / "tooling" / "sw2026"))
SystemLib.path.insert(0, str(WorkRoot / "re" / "tooling" / "sw2026" / "serial"))
"""


KGuard = """
from tests.convert.solidworks.research.ConstructionGuard import BuildAudit

SchemaDir = WorkRoot / "re" / "tooling" / "sw2026" / "serial" / "defs"
AuditGuard = BuildAudit(SchemaDir)
SystemLib.addaudithook(AuditGuard.InspectEvent)
"""


KNative = """
from codecs import lookup as FindCodec
from Core import Obj as NativeObj
from Classes import registry as NewRegistry
from Streams import StreamDoc, store_rooted as StoreRooted, load_rooted as LoadRooted
"""


KBuilders = """
from defs.Definition import (
    load_definition as LoadDefinition,
    store_definition as StoreDefinition,
)
from builders.Model import (
    configuration_manager as NewManager,
    principal_planes as NewPlanes,
    PersistentIds,
)
from builders.Model import (
    relation_manager as NewRelations,
    system_folders as NewFolders,
    detail_cabinet as NewCabinet,
)
"""


KCodec = """
from builders.Definition import (
    part_definition as NewPartDef,
    definition_stream as WritePartDef,
)
from convert.adapters.solidworks.container.Container import (
    build_sldprt as BuildContainer,
    SldprtArchive as ArchiveFile,
)

CodecReg = NewRegistry()
FindCodec("utf-16-le")
FindCodec("latin-1")
AuditGuard.BeginBuild()
"""


KBuild = """
ConfigNames = [NamePrefix + str(IndexValue) for IndexValue in range(CountCfg)]
ManagerNode = NewManager(
    owner=NativeObj("moPart_c"),
    names=ConfigNames,
    date_code=2026306,
    parasolid_version=370108,
    updated_at=1700000000,
)
DocumentDef = NewPartDef(
    density_kg_m3=DensityVal,
    drafting_standard="moISO_c",
    detail_flags=(0, 3, 48),
    tessellation=(20, 15, 3, False),
    system_preference_7a=False,
    journal_name=NamePrefix + " journal",
)
StreamMap = {
    "Contents/CMgr": StoreRooted(
        StreamDoc("rooted", {"base": 1}, [ManagerNode]), CodecReg, 19000
    ),
    "Contents/Definition": WritePartDef(registry=CodecReg, document=DocumentDef),
}
"""


KPlanes = """
IdAllocator = PersistentIds()
PlaneNodes = NewPlanes(
    names={AxisName: NamePrefix + AxisName for AxisName in ("x", "y", "z")},
    owner=NativeObj("moPart_c"),
    allocator=IdAllocator,
    date_code=2026306,
    parasolid_version=370108,
    retain_construction_flag=True,
)
StreamMap["Research/PrincipalPlanes"] = StoreRooted(
    StreamDoc("rooted", {"base": 1}, list(PlaneNodes.values())), CodecReg, 19000
)
NextPlaneId = IdAllocator.next_id
"""


KFolders = """
ClassNames = (
    "moCommentsFolder_c",
    "moDocsFolder_c",
    "moEnvFolder_c",
    "moEqnFolder_c",
    "moFavoriteFolder_c",
    "moHistoryFolder_c",
    "moMaterialFolder_c",
    "moNotesAreaFtrFolder_c",
    "moSelectionSetFolder_c",
    "moSensorFolder_c",
    "moSolidBodyFolder_c",
    "moSurfaceBodyFolder_c",
)
SystemOwner = NativeObj("moPart_c")
SystemOwner.f["f9d0"] = NewRelations(owner=SystemOwner)
FolderNodes = NewFolders(
    names={ClassName: NamePrefix + ClassName for ClassName in ClassNames},
    owner=SystemOwner,
    allocator=IdAllocator,
    date_code=2026306,
    parasolid_version=370108,
    created_at=1700000000,
)
"""


KAnnotations = """
CabinetNode = NewCabinet(
    name=NamePrefix + "annotations",
    owner=SystemOwner,
    allocator=IdAllocator,
    date_code=2026306,
    parasolid_version=370108,
)
StreamMap["Research/SystemFeatures"] = StoreRooted(
    StreamDoc("rooted", {"base": 1}, [*FolderNodes, CabinetNode]), CodecReg, 19000
)
"""


KContainer = """
BinaryFile = BuildContainer(StreamMap)
ContainerFile = ArchiveFile.from_bytes(BinaryFile)
PlaneDocu, PlaneReader = LoadRooted(
    ContainerFile.require("Research/PrincipalPlanes"), CodecReg, 1, 19000
)
if (
    PlaneDocu.tail
    or PlaneReader.left()
    or StoreRooted(PlaneDocu, CodecReg, 19000) != StreamMap["Research/PrincipalPlanes"]
):
    raise RuntimeError("principal plane graph changed after decoding")
SystemDocu, SystemReader = LoadRooted(
    ContainerFile.require("Research/SystemFeatures"), CodecReg, 1, 19000
)
if (
    SystemDocu.tail
    or SystemReader.left()
    or StoreRooted(SystemDocu, CodecReg, 19000) != StreamMap["Research/SystemFeatures"]
):
    raise RuntimeError("system feature graph changed after decoding")
"""


KCheck = """
ConfigDocu, ConfigReader = LoadRooted(
    ContainerFile.require("Contents/CMgr"), CodecReg, 1, 19000
)
DefineDocu, DefineReader = LoadDefinition(
    ContainerFile.require("Contents/Definition"), CodecReg, 19000
)
ManagerRead = ConfigDocu.roots[0]
ConfigNodes = [EntryValue["o"] for EntryValue in ManagerRead["f370"]["items"]]
if ConfigDocu.tail or DefineDocu.tail or ConfigReader.left() or DefineReader.left():
    raise RuntimeError("fresh graph has unread bytes")
if StoreRooted(ConfigDocu, CodecReg, 19000) != StreamMap["Contents/CMgr"]:
    raise RuntimeError("configuration graph changed after decoding")
if StoreDefinition(DefineDocu, CodecReg, 19000) != StreamMap["Contents/Definition"]:
    raise RuntimeError("document graph changed after decoding")
if (
    ManagerRead["f360"] is not ConfigNodes[0]
    or ManagerRead["f368"] is not ConfigNodes[0]
):
    raise RuntimeError("current configuration aliases were not preserved")
"""


KMetrics = """
BuildReport = {
    "configuration_names": [ConfigNode["f18"]["f08"] for ConfigNode in ConfigNodes],
    "configuration_ids": [ConfigNode["f08"] for ConfigNode in ConfigNodes],
    "next_configuration_id": ManagerRead["f40c"],
    "plane_ids": [PlaneNode["f08"] for PlaneNode in PlaneDocu.roots],
    "plane_normals": [PlaneNode["f6f8"]["normal"] for PlaneNode in PlaneDocu.roots],
    "next_plane_id": NextPlaneId,
    "next_persistent_id": IdAllocator.next_id,
    "system_classes": [ModelNode.cls for ModelNode in SystemDocu.roots],
    "system_ids": [ModelNode["f08"] for ModelNode in SystemDocu.roots],
    "folder_times": [
        ((ModelNode["f2a4"] & 4294967295) << 32 | ModelNode["f2a0"] & 4294967295)
        // 10000000
        - 11644473600
        for ModelNode in SystemDocu.roots[:-1]
    ],
}
"""


KReport = """
BuildReport.update(
    {
        "density_kg_m3": DefineDocu.head["f1688"],
        "journal_name": DefineDocu.head["ffd8"]["f18"]["f08"],
        "stream_bytes": {
            StreamName: len(StreamData)
            for (StreamName, StreamData) in StreamMap.items()
        },
        "container_bytes": len(BinaryFile),
        "runtime_reads": AuditGuard.DeniedReads,
        "vendor_loadable": False,
        "application_usable": False,
        "module_reads": AuditGuard.ModuleReads,
        "audit_phase": "imports" if AuditGuard.Importing else "construction",
    }
)
print(EncodeJson(BuildReport, ensure_ascii=True))
"""

KProgram = (
    KImports
    + KGuard
    + KNative
    + KBuilders
    + KCodec
    + KBuild
    + KPlanes
    + KFolders
    + KAnnotations
    + KContainer
    + KCheck
    + KMetrics
    + KReport
)


def RunBuilders(
    Directory: FilePath, Count: int, Density: float, Prefix: str
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-c",
            KProgram,
            str(KRepoRoot),
            str(Count),
            str(Density),
            Prefix,
        ],
        cwd=Directory,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
