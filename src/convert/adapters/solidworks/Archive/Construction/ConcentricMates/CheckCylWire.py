from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream


# independent child linkage must never use a stale generated configuration or header snapshot
def CheckCylWire(ChildValue: PartCandidate) -> None:
    Config, Manager = ChildValue.ConfigValue, ChildValue.SystemValue.ManagerValue
    Resolved = ChildValue.ResolvedValue
    Version = Config.VersionValue
    if Version != 19000 or Resolved.VersionValue != Version:
        raise ValueError("concentric child requires the measured modern archive")
    ConfigBytes, ConfigGraph = WriteConfigMut(
        Config.RootValue, Version, ChildValue.HeaderValue
    )
    ResolvedBytes, _ = WriteResolMut(
        Resolved.RootsValue,
        Resolved.ExtraFields,
        Version,
        ConfigGraph.MapValue,
        Resolved.ContextValue,
    )
    Snapshots = {
        "Contents/Config-0": ConfigBytes,
        KResolvedFeaturesStream: ResolvedBytes,
        "Contents/CMgr": WriteCmgrMut(Manager, Version),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(
            ChildValue.HeaderValue, Version
        ),
        "Header2": WriteHeadGraph(ChildValue.TopHeader, Version),
    }
    if any(
        Content != ChildValue.StreamsValue.get(NameValue)
        for NameValue, Content in Snapshots.items()
    ):
        raise ValueError(
            "concentric child typed links disagree with its generated archive"
        )
