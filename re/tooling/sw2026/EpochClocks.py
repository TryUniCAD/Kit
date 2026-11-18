from __future__ import annotations

from dataclasses import dataclass

from EpochText import read_text
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, FieldText


def require(value, message):
    if not value:
        raise ValueError(message)


def node(value, name):
    require(type(value) is ArchiveNode and value.ClassValue == RuntimeClass(name, 1),
            "epoch experiment requires actual concrete " + name)
    return value


def drawing_clocks(value):
    names = set(ClockPlan.__dataclass_fields__) - {"ManagerSavedAt"}
    require(type(value) is dict and set(value) == names,
            "drawing clock model must omit the nonexistent independent manager header")
    require(all(type(item) is int and 946684800 <= item < 4102444800 for item in value.values()),
            "drawing discovery clocks require explicit modern integer wall seconds")
    require(value["CreatedAt"] == value["SelfCreatedAt"] == value["RootFirstEventAt"]
            == value["VersionHistoryFirstEventAt"] and value["ModifiedAt"] >= value["CreatedAt"]
            and value["SelfSavedAt"] >= value["ModifiedAt"],
            "epoch discovery leaves the existing coupled drawing construction policy unchanged")
    return dict(value)


@dataclass(frozen=True, slots=True)
class ClockPlan:
    CreatedAt: int
    ModifiedAt: int
    UpdatedAt: int
    RootFirstEventAt: int
    VersionHistoryFirstEventAt: int
    SelfCreatedAt: int
    SelfSavedAt: int
    ManagerSavedAt: int

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            require(type(value) is int and 946684800 <= value < 4102444800,
                    "epoch discovery clock must be explicit integer wall seconds in the modern non-sentinel experiment range: " + name)
        require(self.CreatedAt == self.SelfCreatedAt,
                "epoch discovery preserves header and self creation identity")
        require(self.SelfSavedAt >= max(self.CreatedAt, self.ModifiedAt),
                "epoch discovery preserves the existing self-save ordering boundary")

    @classmethod
    def from_data(cls, value):
        require(type(value) is dict and set(value) == set(cls.__dataclass_fields__),
                "epoch discovery requires the complete explicit clock model")
        return cls(**value)

    def to_data(self):
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


def root_events(header, owner):
    node(header, "moHeader_c")
    identifier = FieldInt(owner.FieldsValue, "f08")
    name = FieldText(node(owner.FieldsValue["f18"], "moNodeName_c").FieldsValue, "f08")
    logs = ReadLogItems(header.FieldsValue["f20"], "moLogs_c")
    matching = tuple(value for value in logs if FieldInt(value.FieldsValue, "f48") == identifier)
    require(len(matching) == 1 and read_text(matching[0].FieldsValue["f50"], "moLogs_c.f50", nonempty=True) == name,
            "epoch header must retain its actual model id and root log name")
    events = ReadLogItems(matching[0], "moStamp_c")
    require(0 < len(events) <= 128, "epoch root log has missing or unbounded events")
    return events


def apply_before_emit(headers, owner, plan, settings):
    require(type(plan) is ClockPlan, "epoch construction requires an explicit ClockPlan")
    require(plan.CreatedAt == settings.HeaderValue.CreatedAt == settings.SystemValue.CreatedAt
            and plan.UpdatedAt == settings.HeaderValue.UpdatedAt
            and plan.SelfSavedAt == settings.OutputValue.SavedAt == plan.ManagerSavedAt,
            "epoch experiment only varies archive time and initial root or history event")
    header, top, manager = headers
    self_value = node(header.FieldsValue["f38"], "moExtObject_c")
    require(top.FieldsValue["f38"] is self_value,
            "fresh epoch headers must retain their one actual self-file alias")
    shared = self_value.FieldsValue["shared"]
    require(type(shared) is dict and FieldInt(shared, "f28") == plan.SelfCreatedAt
            and FieldInt(self_value.FieldsValue, "f60") == plan.SelfSavedAt
            and FieldInt(node(manager, "dmConfigMgrHeader_c").FieldsValue, "f60") == plan.ManagerSavedAt,
            "epoch discovery does not replace unrelated self or manager provenance")
    for value in (header, top):
        require(FieldInt(value.FieldsValue, "f70") == plan.CreatedAt,
                "fresh header creation differs from the independently authored clock model")
        events = root_events(value, owner)
        require(len(events) == 1 and FieldInt(events[0].FieldsValue, "f18") == plan.CreatedAt,
                "clock composition requires the actual fresh root event before serialization")
        value.FieldsValue["f50"] = plan.ModifiedAt
        value.FieldsValue["f48"] = plan.UpdatedAt
        events[0].FieldsValue["f18"] = plan.RootFirstEventAt
    require(root_events(header, owner)[0] is not root_events(top, owner)[0],
            "separate fresh header streams must not borrow another root event node")
    return {"actual_shared_self_alias": True, "separate_root_events": True,
            "root_id": FieldInt(owner.FieldsValue, "f08"),
            "before_first_stream_serialization": True}
