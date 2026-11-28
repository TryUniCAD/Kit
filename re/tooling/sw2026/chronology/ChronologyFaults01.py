from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.Chronology.HeaderClocks import HeaderClocks
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import MakeFeatTime
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeIntentHead import MakeIntentHead
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import RevisionBook
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionEvent import RevisionEvent
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionLog import RevisionLog
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


def rejected(candidate, name):
    model = candidate["system"].RootValue
    book = candidate["book"]
    clocks = candidate["clocks"]
    root = book.LogsValue[0]
    event = root.EventsValue[0]
    helper = next(value for value in candidate["system"].FeatureValues if value.ClassValue.NameValue == "moCommentsFolder_c")
    if name == "duplicate_log_owner":
        book = replace(book, LogsValue=(root, root))
    elif name == "foreign_feature_owner":
        foreign = ArchiveNode(model.ClassValue, dict(model.FieldsValue))
        invalid = ArchiveNode(helper.ClassValue, dict(helper.FieldsValue, owner=foreign))
        book = replace(book, LogsValue=(root, RevisionLog(invalid, "Foreign semantic owner", (event,))))
    elif name == "missing_model_event":
        book = replace(book, LogsValue=(RevisionLog(helper, "Helper only", (event,)),))
    elif name == "modified_first_model_event":
        book = replace(book, LogsValue=(replace(root, EventsValue=(replace(event, OperationValue="modified"),)),))
    elif name == "unsupported_owner_class":
        invalid = ArchiveNode(RuntimeClass("moCamera_c", 1), dict(helper.FieldsValue))
        book = replace(book, LogsValue=(root, RevisionLog(invalid, "Unknown class", (event,))))
    elif name == "owner_schema":
        invalid = ArchiveNode(RuntimeClass(helper.ClassValue.NameValue, 2), dict(helper.FieldsValue))
        book = replace(book, LogsValue=(root, RevisionLog(invalid, "Wrong schema", (event,))))
    elif name == "distinct_owner_same_identifier":
        invalid = ArchiveNode(helper.ClassValue, dict(helper.FieldsValue, f08=model.FieldsValue["f08"]))
        book = replace(book, LogsValue=(root, RevisionLog(invalid, "Duplicate id", (event,))))
    elif name == "boolean_identifier":
        invalid = ArchiveNode(helper.ClassValue, dict(helper.FieldsValue, f08=True))
        book = replace(book, LogsValue=(root, RevisionLog(invalid, "Boolean id", (event,))))
    elif name == "unnamed_owner":
        invalid = ArchiveNode(helper.ClassValue, dict(helper.FieldsValue, f18=None))
        book = replace(book, LogsValue=(root, RevisionLog(invalid, "No actual name", (event,))))
    elif name == "duplicate_author_names":
        book = replace(book, UsersValue=(event.UserName, event.UserName))
    elif name == "unresolved_author":
        book = replace(book, LogsValue=(replace(root, EventsValue=(replace(event, UserName="No matching table entry"),)),))
    elif name == "unsupported_revision_status":
        event = replace(event, OperationValue="deleted")
    elif name == "boolean_event_time":
        event = replace(event, EventAt=True)
    elif name == "sentinel_archive_time":
        clocks = replace(clocks, ArchiveAt=2592000)
    elif name == "overflow_event_time":
        event = replace(event, EventAt=0x100000000)
    elif name == "fractional_tick_overflow":
        MakeFeatTime(FeatureInstant(clocks.CreatedAt, 10_000_000))
    elif name == "boolean_feature_time":
        MakeFeatTime(FeatureInstant(True, 0))
    elif name == "negative_fraction":
        MakeFeatTime(FeatureInstant(clocks.CreatedAt, -1))
    else:
        raise AssertionError("unknown explicitly declared fault")
    return MakeIntentHead(model, clocks, book, candidate["allocator"], True)
