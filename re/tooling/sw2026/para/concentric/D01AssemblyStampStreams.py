from ProjectD01Concentric import require
from D01AssemblyPropertyIntent import configuration_and_save

from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Reading.ReadNodeTagMut import ReadNodeTagMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadRows
from convert.adapters.solidworks.Container.Bookkeeping import (
    EncodePartMeta, KConfigObjects, KDisplayUpdate, KModelStamps, PartStamps,
)


STAMP_KEYS = frozenset((KConfigObjects, KDisplayUpdate, KModelStamps))


def require_null(cursor, label):
    tag = ReadNodeTagMut(cursor, 0, 1, RequireCanonicalTags=True)
    require(tag.KindValue == "Null", label + " has an unqualified object")


def read_streams(streams):
    require(STAMP_KEYS <= streams.keys(), "assembly bookkeeping scope is incomplete")
    model = BinaryReader(streams[KModelStamps])
    stamps = PartStamps(*(model.ReadUnsigned(4) for _ in range(3)))
    require(not model.GetRemaining(), "model stamp stream has trailing content")

    display = BinaryReader(streams[KDisplayUpdate])
    update = display.ReadUnsigned(4)
    require_null(display, "display update")
    require(not display.GetRemaining() and update == stamps.update,
            "display update disagrees with the model update counter")

    config = BinaryReader(streams[KConfigObjects])
    require(config.ReadUnsigned(2) == 0, "configuration object overrides have an unqualified prefix")
    require_null(config, "configuration objects")
    require((ReadCStringMut(config), ReadCStringMut(config)) == (CStringValue("", True),) * 2
            and not config.GetRemaining(), "configuration object overrides contain an unqualified name or trailing data")
    return stamps


def root_creation(header, root_id):
    fields = header.FieldsValue
    require(fields.get("f20") is not None, "assembly bookkeeping lacks an owned revision log")
    logs = tuple(log for log in ReadLogItems(fields["f20"], "moLogs_c")
                 if FieldInt(log.FieldsValue, "f48") == root_id)
    require(len(logs) == 1, "assembly bookkeeping requires exactly one root revision log")
    events = ReadLogItems(logs[0], "moStamp_c")
    require(events and FieldInt(events[0].FieldsValue, "f08") == 0,
            "assembly bookkeeping requires the actual root creation event")
    return FieldInt(events[0].FieldsValue, "f18")


def header_stamps(root, config, headers):
    require(root.ClassValue == RuntimeClass("moAssembly_c", 1),
            "assembly stamps require their actual assembly root")
    _, saved_at = configuration_and_save(config, headers)
    root_id = FieldInt(root.FieldsValue, "f08")
    events = tuple(root_creation(header, root_id) for header in headers)
    values = tuple(PartStamps(*(FieldInt(header.FieldsValue, field) for field in ("f70", "f40", "f44")))
                   for header in headers)
    require(values[0] == values[1], "assembly header creation/update/body ownership disagrees")
    require(events[0] == events[1] and all(0 < event <= value.creation_time
            <= FieldInt(header.FieldsValue, "f48") <= saved_at
            for event, value, header in zip(events, values, headers, strict=True)),
            "assembly stamp creation, update or save does not join its actual revision event")
    return values[0]


def add_stamp_streams(streams, state, headers):
    manager = state.ManagerValue.FieldsValue
    config = state.CurrentConfig
    selected, = ReadRows(manager["f370"]["items"])
    require(selected["o"] is manager["f360"] is manager["f368"] is config
            and manager["f370"]["n"] == 1,
            "empty configuration objects require the actual one selected assembly configuration")
    require(not streams.keys() & STAMP_KEYS, "assembly bookkeeping conflicts with an already emitted stream")
    stamps = header_stamps(state.RootValue, config, headers)
    return streams | EncodePartMeta(19000, stamps)
