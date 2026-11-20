from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberGraph import (
    CfgMemberGraph,
)
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KAllMemberSchemas,
    KCfgMemberSchemas,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckCfgMember import (
    CheckCfgMember,
)
from convert.adapters.solidworks.Archive.Config.Members.MemberLayouts import (
    KMemberLayouts,
)
from convert.adapters.solidworks.Archive.Config.Members.MemberVirtuals import (
    KMemberVirtuals,
)
from convert.adapters.solidworks.Archive.Config.Members.ReadMemBodyMut import (
    ReadMemBodyMut,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# bounded member bytes and an explicit caller role must agree before exposing the map
def ReadCfgMember(
    BufferValue: bytes,
    VersionValue: int,
    SeedValue: MapSnapshot,
    MemberClass: RuntimeClass,
) -> CfgMemberGraph:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported(
            "SOLIDWORKS configuration member requires archive version 19000"
        )
    if MemberClass.SchemaValue not in KCfgMemberSchemas.get(MemberClass.NameValue, ()):
        raise BodyUnsupported("SOLIDWORKS configuration member has an unsupported role")
    ContextValue = BodyContext(
        VersionValue, KMemberLayouts, KMemberVirtuals, KAllMemberSchemas
    )
    MapValue = ArchiveMaps(SeedValue.CounterValue, SeedValue)
    ReaderValue = GraphReader(
        BinaryReader(BufferValue),
        MapValue,
        PartialValue(ReadMemBodyMut, ContextValue, MemberClass),
    )
    RootValue = ReadNodeMut(ReaderValue)
    if ReaderValue.Cursor.GetRemaining():
        raise BodyUnsupported("SOLIDWORKS configuration member has trailing data")
    CheckCfgMember(RootValue, MemberClass, MapValue)
    ContextValue.UsageValue.IsComplete = True
    return CfgMemberGraph(
        RootValue, MapValue.Snapshot(), GetBodyReport(ContextValue.UsageValue)
    )
