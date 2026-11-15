from __future__ import annotations

from Core import Obj
from Schema import Registry
from defs.ConfigPart import load_config as LoadConfig
from defs.ResolvedCore import load_resolved as LoadResolved

from convert.adapters.solidworks.container.Container import SldprtArchive


# decoded profile relationships expose ownership defects that byte identity alone cannot detect
def ReadProfiles(
    ArchiveFile: SldprtArchive, CodecReg: Registry
) -> tuple[Obj, list[Obj]]:
    ConfigDocu, ConfigReader = LoadConfig(
        ArchiveFile.require("Contents/Config-0"),
        CodecReg,
        19000,
        archive=ArchiveFile,
    )
    ProfileDocu, ProfileReader = LoadResolved(
        ArchiveFile.require("Contents/Config-0-ResolvedFeatures"),
        CodecReg,
        19000,
        archive=ArchiveFile,
        name="Contents/Config-0-ResolvedFeatures",
        seed=ConfigReader.map_state(),
    )
    if (
        ConfigDocu.tail
        or ProfileDocu.tail
        or ConfigReader.left()
        or ProfileReader.left()
    ):
        raise RuntimeError("constructed profile ownership has unread bytes")
    return ConfigDocu.roots[0], [
        Feature
        for Feature in ProfileDocu.roots
        if Feature.cls in ("moOriginProfileFeature_c", "moProfileFeature_c")
    ]
