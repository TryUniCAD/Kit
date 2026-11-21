from __future__ import annotations

from EpochClocks import require
from EpochText import read_text
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, FieldText


def concrete(value, name):
    require(type(value) is ArchiveNode and value.ClassValue == RuntimeClass(name, 1),
            "clock readback requires actual concrete " + name)
    return value


def stamp_record(value):
    fields = value.FieldsValue if type(value) is ArchiveNode else value
    require(type(fields) is dict or hasattr(fields, "keys"), "clock event is not an actual typed field record")
    return {key: FieldInt(fields, key) for key in ("f08", "f0c", "f10", "f18")} | {
        "f20": read_text(fields["f20"], "moStamp_c.f20")}


def observe_header(header, owner):
    header = concrete(header, "moHeader_c")
    fields = header.FieldsValue
    identity = FieldInt(owner.FieldsValue, "f08")
    name = FieldText(concrete(owner.FieldsValue["f18"], "moNodeName_c").FieldsValue, "f08")
    all_logs = ReadLogItems(fields["f20"], "moLogs_c")
    require(len(all_logs) <= 4096, "clock readback log inventory exceeds its declared bound")
    logs = []
    root = []
    for log in all_logs:
        log_id = FieldInt(log.FieldsValue, "f48")
        events = ReadLogItems(log, "moStamp_c")
        require(len(events) <= 128, "clock readback event inventory exceeds its declared bound")
        row = {"owner_id": log_id, "owner_name": read_text(log.FieldsValue["f50"], "moLogs_c.f50", nonempty=True),
               "events": [stamp_record(value) for value in events]}
        logs.append(row)
        if log_id == identity:
            root.append(row)
    require(len(root) == 1 and root[0]["events"],
            "clock readback root event does not belong to the actual model")
    self_value = concrete(fields["f38"], "moExtObject_c")
    shared = self_value.FieldsValue["shared"]
    return {"CreatedAt": FieldInt(fields, "f70"), "ModifiedAt": FieldInt(fields, "f50"),
            "UpdatedAt": FieldInt(fields, "f48"), "SelfCreatedAt": FieldInt(shared, "f28"),
            "SelfSavedAt": FieldInt(self_value.FieldsValue, "f60"),
            "RootFirstEventAt": root[0]["events"][0]["f18"],
            "model_id": identity, "model_name": name, "all_logs": logs,
            "root_log_name_matches_model": root[0]["owner_name"] == name,
            "actual_root_event_count": len(root[0]["events"]),
            "self_creation_equals_header": FieldInt(shared, "f28") == FieldInt(fields, "f70")}


def observe_history(root):
    root = concrete(root, "moVersionHistory_c")
    fields = root.FieldsValue
    rows = fields["states"]
    require(type(rows) in (tuple, list) and 0 < len(rows) <= 128 and FieldInt(fields, "n") == len(rows),
            "clock readback version history has invalid membership or length")
    return {"states": [{"stamp": stamp_record(row["st"]["f08"]),
                        "file_version": FieldInt(row["st"], "f30")} for row in rows],
            "VersionHistoryFirstEventAt": FieldInt(rows[0]["st"]["f08"], "f18"),
            "history_state_count": len(rows)}


def require_clocks(header, history, manager, expected):
    require(set(expected) == {"CreatedAt", "ModifiedAt", "UpdatedAt", "RootFirstEventAt",
                              "VersionHistoryFirstEventAt", "SelfCreatedAt", "SelfSavedAt", "ManagerSavedAt"},
            "independent clock readback expected model is incomplete")
    observed = {key: header[key] for key in expected if key not in ("VersionHistoryFirstEventAt", "ManagerSavedAt")}
    observed["VersionHistoryFirstEventAt"] = history["VersionHistoryFirstEventAt"]
    observed["ManagerSavedAt"] = FieldInt(concrete(manager, "dmConfigMgrHeader_c").FieldsValue, "f60")
    require(observed == expected, "independent typed clock readback differs from the modeled event owners: " + repr(observed))
    require(header["self_creation_equals_header"] and header["root_log_name_matches_model"]
            and header["actual_root_event_count"] == 1
            and history["history_state_count"] == 1,
            "fresh clock candidate introduced an undeclared event or self identity")
    return observed
