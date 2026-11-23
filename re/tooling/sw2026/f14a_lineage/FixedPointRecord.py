from functools import partial
from math import isfinite

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import DatumPoint
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

FEATURE = RuntimeClass("moRefPoint_c", 1)
DATA = RuntimeClass("moRefPointData_c", 1)
VIRTUAL_SLOTS = (0x3E8, 0x3F8, 0x4B8, 0x4C0)
LAYOUTS = {
    FEATURE.NameValue: (
        NativeField("Base", "moRefGeom_c"),
        NativeField("Node", "f700", DATA.NameValue),
        NativeField("Node", "f6f8", "moProfileFeature_c"),
        NativeField("Node", "f708", "moSurfaceRef_w"),
    ),
    DATA.NameValue: (),
}


def context(stock):
    resolved = stock.ResolvedValue
    config = stock.ConfigValue
    assert config.VersionValue == resolved.VersionValue == 19000
    model = MakeResolvedCtx(19000, config.MapValue, resolved.ContextValue, None)
    assert model.PartRootValue is stock.SystemValue.RootValue
    assert not set(LAYOUTS) & set(model.LayoutsValue)
    model.LayoutsValue = {**model.LayoutsValue, **LAYOUTS}
    model.SchemasValue = {**model.SchemasValue, **dict.fromkeys(LAYOUTS, (1,))}
    model.VirtualValue = {
        **model.VirtualValue,
        **{(FEATURE.NameValue, slot): model.VirtualValue[("moRefAxis_c", slot)] for slot in VIRTUAL_SLOTS},
    }
    return model


def fixed_point(stock, label, xyz_mm, epoch):
    if (
        type(xyz_mm) is not tuple
        or len(xyz_mm) != 3
        or not all(type(value) in (float, int) and isfinite(value) for value in xyz_mm)
        or type(label) is not str
        or not label or label != label.strip()
        or not label.isascii() or not label.isprintable()
    ):
        raise ValueError("fixed reference point requires a named finite coordinate")
    root = stock.SystemValue.RootValue
    if label in {ReadNodeName(node) for node in stock.ResolvedValue.RootsValue if node is not None}:
        raise ValueError("fixed reference point needs a distinct feature name")
    start = FieldInt(stock.CurrentConfig.FieldsValue, "f85c") + 1
    if start != FieldInt(stock.TopHeader.FieldsValue, "f08"):
        raise ValueError("fixed reference point needs the actual stock allocator handoff")
    allocator = PersistentIds(start)
    target = MakePartRecipe(stock.PlanValue, epoch).TargetValue
    feature = ArchiveNode(FEATURE, {})
    InitFeatureMut(feature, label, root, target, allocator)
    fields = feature.FieldsValue
    fields.update(dict.fromkeys(KAtomWords, 0))
    fields.update({key: [] for key in KAtomLists})
    fields.update(
        f35c=0,
        f368={"n": 0, "items": []},
        f388={"n": 0, "items": []},
        f538=None,
        f4a0=1,
        f6c0=DatumPoint(tuple(component * 0.001 for component in xyz_mm)),
        f6dc=4,
        f6e0=0,
        f6e8=None,
        f6f0=0,
        f700=ArchiveNode(DATA, {}),
        f6f8=None,
        f708=None,
    )
    return feature


def encode(stock, point):
    seed = stock.ResolvedValue.MapValue
    if point.ClassValue != FEATURE or point.FieldsValue.get("owner") is not stock.SystemValue.RootValue:
        raise ValueError("fixed point requires its actual part owner")
    writer = BodyWriter(ArchiveMaps(seed.CounterValue, seed), context(stock), WriteBodyMut)
    WriteNodeMut(writer, point)
    return bytes(writer.OutputValue), writer.MapValue.Snapshot()


def decode(stock, payload):
    seed = stock.ResolvedValue.MapValue
    cursor = BinaryReader(payload)
    reader = GraphReader(
        cursor, ArchiveMaps(seed.CounterValue, seed), partial(ReadBodyMut, context(stock))
    )
    point = ReadNodeMut(reader)
    if point is None or cursor.GetRemaining():
        raise ValueError("fixed reference point bytes have a different graph boundary")
    fields = point.FieldsValue
    location = fields.get("f6c0")
    data = fields.get("f700")
    if (
        point.ClassValue != FEATURE or "owner" in fields
        or fields.get("f08") != stock.TopHeader.FieldsValue.get("f08")
        or not isinstance(location, dict) or set(location) != {"x", "y", "z"}
        or not all(type(value) is float and isfinite(value) for value in location.values())
        or not isinstance(data, ArchiveNode) or data.ClassValue != DATA or data.FieldsValue
        or any(fields.get(key) is not None for key in ("f6e8", "f6f8", "f708"))
        or not ReadNodeName(point) or fields.get("f4a0") != 1
        or fields.get("f6dc") != 4 or fields.get("hidden") != 0
        or fields.get("f6e0") != 0 or fields.get("f6f0") != 0
    ):
        raise ValueError("fixed reference point has another actual graph owner or mode")
    fields["owner"] = stock.SystemValue.RootValue
    return point, reader.MapValue.Snapshot()
