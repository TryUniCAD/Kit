from TraceCfgFinish import field_digest, source
from convert.adapters.solidworks.Archive.Maps.AddEntryMut import AddEntryMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.FindClass import FindClass
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNodeTagMut import ReadNodeTagMut
from convert.adapters.solidworks.Archive.Reading.ReadTypeDescMut import ReadTypeDescMut

require = source.require


def map_checkpoint(role, maps):
    slots = list(maps.EntryMap)
    require(slots == list(range(1, maps.CounterValue)) and maps.BaseValue == 4,
            "native finish checkpoint has an incomplete or reordered map")
    rows = []
    for slot, cell in maps.EntryMap.items():
        item = cell.EntryValue
        if isinstance(item, (RuntimeClass, ExternalClass)):
            require(maps.ClassLookup.get(item) == slot, "native class inverse lookup differs from its slot")
            kind, descriptor, index = "class", item, None
        else:
            require(isinstance(item, ArchiveNode) and maps.ObjectLookup.get(id(item)) == slot,
                    "native object inverse lookup differs from its slot")
            kind, descriptor, index = "object", item.ClassValue, item.IndexValue
        definition = descriptor.SchemaValue if isinstance(descriptor, RuntimeClass) else descriptor.IndexValue
        rows.append([slot, kind, descriptor.NameValue, type(descriptor).__name__, definition, index])
    classes, objects = len(maps.ClassLookup), len(maps.ObjectLookup)
    require(classes + objects == len(slots) and classes > 0 and objects > 0, "native finish map lost mixed membership")
    return {"role": role, "base": maps.BaseValue, "counter": maps.CounterValue,
            "slots": slots, "classes": classes, "objects": objects, "slot_sha256": field_digest(rows)}


def birth_offsets(maps):
    offsets = [entry.EntryValue.StartOffset for slot, entry in maps.EntryMap.items()
               if slot >= maps.BaseValue and isinstance(entry.EntryValue, ArchiveNode)]
    require(all(type(offset) is int for offset in offsets), "native object has no physical birth tag")
    return offsets


def map_tag(maps, cursor):
    start = cursor.GetOffset()
    tag = ReadNodeTagMut(cursor, 0, 1, RequireCanonicalTags=True)
    if tag.KindValue == "NewClass":
        descriptor = ReadTypeDescMut(cursor, CanonicalMap=maps)
        AddEntryMut(maps, descriptor)
    elif tag.KindValue == "ClassRef" and tag.IndexValue is not None:
        descriptor = FindClass(maps, tag.IndexValue)
    else:
        raise ValueError("finish map locator does not point to an object allocation")
    require(isinstance(descriptor, RuntimeClass), "finish map locator uses an unmaterialized class")
    node = ArchiveNode(descriptor, {}, StartOffset=start, IndexValue=maps.CounterValue)
    AddEntryMut(maps, node)


def project_map(config, seed, offsets, stop):
    maps = ArchiveMaps(seed.BaseValue, seed.MapValue)
    require(type(offsets) is list and offsets and all(type(offset) is int for offset in offsets)
            and all(seed.LightOffset <= offset < stop for offset in offsets)
            and offsets == sorted(set(offsets)), "finish allocation locators cross their section boundary")
    for first, last in zip(offsets, offsets[1:] + [stop], strict=True):
        cursor = BinaryReader(config, first, last)
        map_tag(maps, cursor)
    require(birth_offsets(maps) == offsets, "finish allocation changed the ordered tag locators")
    return maps
