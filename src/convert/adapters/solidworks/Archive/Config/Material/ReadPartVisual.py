from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Config.Material.CfgVisualGraph import (
    CfgVisualGraph,
)
from convert.adapters.solidworks.Archive.Config.Material.CheckMatVisual import (
    CheckMatVisual,
)
from convert.adapters.solidworks.Archive.Config.Material.MatVisualTypes import (
    KMatVisualClass,
    KMatVisualSchemas,
)
from convert.adapters.solidworks.Archive.Config.Material.PartVisLayouts import (
    KPartVisLayouts,
)
from convert.adapters.solidworks.Archive.Config.Material.ReadVisBodyMut import (
    ReadVisBodyMut,
)
from convert.adapters.solidworks.Archive.Config.Material.RequireMatNode import (
    RequireMatNode,
)
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import KNodeNameClass
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Container.Container import SldprtArchive


# physical part visual inspection starts after the real header handoff and stops after its complete local member
def ReadPartVisual(ArchiveValue: SldprtArchive) -> CfgVisualGraph:
    StartValue = ReadPartStart(ArchiveValue)
    PrefixMap = StartValue.MapValue
    MapValue = ArchiveMaps(PrefixMap.CounterValue, PrefixMap)
    Cursor = BinaryReader(
        ArchiveValue.Require("Contents/Config-0"),
        StartValue.LightOffset,
        StartValue.LightOffset + StartValue.LightSize,
    )
    ContextValue = BodyContext(KHeaderVersion, KPartVisLayouts, {}, KMatVisualSchemas)
    BodyReader = PartialValue(ReadVisBodyMut, ContextValue)
    ReaderValue = GraphReader(Cursor, MapValue, BodyReader, NestingDepth=1)
    ModelValue = StartValue.RootValue
    ReadBodyMut(ContextValue, ReaderValue, ModelValue)
    FieldsValue = ModelValue.FieldsValue
    _ = RequireMatNode(
        FieldsValue["f18"], MapValue, KNodeNameClass, PrefixMap.CounterValue
    )
    VisualValue = RequireMatNode(
        FieldsValue["f78"], MapValue, KMatVisualClass, PrefixMap.CounterValue
    )
    CheckMatVisual(VisualValue)
    ContextValue.UsageValue.IsComplete = True
    return CfgVisualGraph(
        StartValue,
        VisualValue,
        MapValue.Snapshot(),
        Cursor.GetOffset(),
        GetBodyReport(ContextValue.UsageValue),
    )
