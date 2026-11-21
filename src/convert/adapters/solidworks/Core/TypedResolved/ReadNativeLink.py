from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KitResolvedStream
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqConfig import (
    CheckEqConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# public semantic reads must enter through the same proven configuration and resolved alias chain
def ReadNativeLink(
    Archive: SldprtArchive,
    ConfigId: int | None,
    *,
    RelationConfig: str | None = None,
    ReadFillets: bool = False,
) -> NativeLink:
    VersionValue = ContainerMo(Archive.streams)
    if (
        VersionValue != 19000
        or ConfigId != 0
        or Archive.format_version != 4
        or KitResolvedStream in Archive.streams
        or (ReadFillets and RelationConfig is not None)
    ):
        raise BodyUnsupported(
            "typed model semantics require ordinary version 19000 Config-0"
        )
    ConfigName = "Contents/Config-0"
    StreamName = ConfigName + "-ResolvedFeatures"
    HeaderValue = ReadHeaderGraph(
        Archive.require(ConfigName + "-ModelHeader"), VersionValue
    )
    ConfigValue = ReadConfigMut(
        Archive.require(ConfigName),
        VersionValue,
        HeaderValue,
        PartRelations=RelationConfig is not None,
    )
    ManagerValue = ReadCmgrMut(Archive.require("Contents/CMgr"), VersionValue)
    if RelationConfig is not None:
        CheckEqConfig(ManagerValue.RootValue, RelationConfig)
    ResolvedValue = ReadResolvedMut(
        Archive.require(StreamName),
        VersionValue,
        ConfigValue.MapValue,
        MakeLinkContext(ConfigValue, ManagerValue),
        ReadFillets=ReadFillets,
    )
    return NativeLink(ConfigValue, ResolvedValue, ConfigName, StreamName)
