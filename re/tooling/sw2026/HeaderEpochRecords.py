from dataclasses import replace

from builders.HeaderGraphBridge import generated_header_bytes
from builders.Metadata import revision_log
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


EPOCHS = (1794700000, 1794707654)


def sdk_log(datum, epochs):
    events = tuple(ArchiveNode(RuntimeClass("moStamp_c", 1), {"f08": 0, "f0c": 0, "f10": 0, "f18": epoch, "f20": CStringValue("authored datum event", True)}) for epoch in epochs)
    return ArchiveNode(RuntimeClass("moLogs_c", 1), {"items": events, "f48": datum["f08"], "f50": CStringValue(datum["f18"]["f08"], True)})


def author_history(child, settings):
    scenario = settings["case"]
    if scenario == "absent":
        return child
    datum, = (value for value in child.features if value.cls == "moRefPlane_c" and value["f18"]["f08"] == settings["datum"])
    epochs = () if scenario == "empty" else EPOCHS
    events = [{"f08": 0, "f0c": 0, "f10": 0, "f18": epoch, "f20": "authored datum event"} for epoch in epochs]
    log = revision_log(object_id=datum["f08"], name=datum["f18"]["f08"], entries=events)
    rows = child.model_header["f20"]["items"]
    rows.append({"o": log})
    child.model_header["f20"]["n"] = len(rows)
    streams = dict(child.streams)
    streams["Contents/Config-0-ModelHeader"] = generated_header_bytes(child.model_header, 19000)
    header = ReadHeaderGraph(streams["Header2"], 19000)
    header.FieldsValue["f20"].FieldsValue["items"] += (sdk_log(datum, epochs),)
    streams["Header2"] = WriteHeadGraph(header, 19000)
    return replace(child, streams=streams)


def header_fault(header, settings, datum_id):
    name = settings.get("fault")
    if name is None:
        return
    container = header.FieldsValue["f20"]
    fields = container.FieldsValue if isinstance(container, ArchiveNode) else container
    items = fields["items"]
    direct = all(isinstance(value, ArchiveNode) for value in items)
    rows = [value if isinstance(value, ArchiveNode) else value["o"] for value in items]
    selected, = (value for value in rows if value.FieldsValue["f48"] == datum_id)
    selected_fields = selected.FieldsValue
    events = selected_fields["items"]
    first = events[0] if isinstance(events[0], ArchiveNode) else events[0]["o"]
    if name == "duplicate_log":
        fields["items"] = (*items, selected if direct else {"o": selected})
        if "n" in fields:
            fields["n"] = len(fields["items"])
    elif name == "invalid_epoch":
        first.FieldsValue["f18"] = -1
    elif name == "overflow_epoch":
        first.FieldsValue["f18"] = 1 << 32
    elif name == "boolean_epoch":
        first.FieldsValue["f18"] = True
    elif name == "wrong_log_class":
        selected.ClassValue = RuntimeClass("moStamp_c", 1)
    elif name == "wrong_stamp_class":
        first.ClassValue = RuntimeClass("moLogs_c", 1)
    elif name == "wrong_log_schema":
        selected.ClassValue = RuntimeClass("moLogs_c", 2)
    elif name == "wrong_stamp_schema":
        first.ClassValue = RuntimeClass("moStamp_c", 2)
    elif name == "invalid_items":
        fields["items"] = None
    elif name == "wrong_count":
        fields["n"] = len(items) + 1
    elif name == "wrong_list_owner":
        container.ClassValue = RuntimeClass("moExtObjectList_c", 1)
    elif name == "bad_row":
        fields["items"] = ({"unrelated": selected},)
        if "n" in fields:
            fields["n"] = 1
    else:
        raise ValueError("unknown header epoch fault")
