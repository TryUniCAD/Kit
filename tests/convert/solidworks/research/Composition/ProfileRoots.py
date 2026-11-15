from __future__ import annotations

from importlib import import_module as ImportModule
from typing import cast as CastValue

from convert.adapters.solidworks.container.Container import SldprtArchive

# research schemas resolve after the child process establishes its explicit import paths
KLoadConfig = ImportModule("defs.ConfigPart").load_config

# resolved decoding must use the same initialized research modules as the child constructor
KLoadResolved = ImportModule("defs.ResolvedCore").load_resolved


# decoded profile relationships expose ownership defects that byte identity alone cannot detect
def ReadProfiles(
    ArchiveFile: SldprtArchive, CodecReg: object
) -> tuple[object, list[object]]:
    ConfigDocu, ConfigReader = KLoadConfig(
        ArchiveFile.require("Contents/Config-0"),
        CodecReg,
        19000,
        archive=ArchiveFile,
    )
    ProfileDocu, ProfileReader = KLoadResolved(
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
    return CastValue(object, ConfigDocu.roots[0]), [
        Feature
        for Feature in CastValue(list[object], ProfileDocu.roots)
        if getattr(Feature, "cls", None)
        in ("moOriginProfileFeature_c", "moProfileFeature_c")
    ]
