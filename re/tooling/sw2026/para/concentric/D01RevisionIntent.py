from dataclasses import asdict

from ProjectD01Concentric import require

from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeywordName import AsmKeywordName
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.Chronology.HeaderClocks import HeaderClocks
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import MakeFeatTime
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeRevBook import MakeRevBook
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import RevisionBook
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionEvent import RevisionEvent
from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionLog import RevisionLog
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadRows, RequireNode
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import ReadMemberTime
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren


MODEL = ("model", "moAssembly_c", "")
EXPLODED = ("exploded", "moExplViewManager_c", "")
EVENT_OPS = {0: "created", 1: "modified"}


def only_kind(nodes, kind):
    found = tuple(row for row in nodes if row.ClassValue == RuntimeClass(kind, 1))
    require(len(found) == 1, f"chronology requires one actual {kind}")
    return found[0]


def ordered_occurrences(root):
    return tuple(row["o"] for row in ReadRows(root.FieldsValue["f68"]["list"]["items"]))


def owners(root, resolved, refs, mates, *, constructed=False):
    require(root.ClassValue == RuntimeClass("moAssembly_c", 1)
            and type(resolved) is tuple and len(resolved) == 16
            and type(refs) is tuple and len(refs) == 2 and refs == ordered_occurrences(root)
            and type(mates) is tuple and len(mates) == 1,
            "chronology requires the scoped real root, feature list, occurrences and separate mate list")
    env = only_kind(resolved, "moEnvFolder_c")
    cabinet = only_kind(resolved, "moDetailCabinet_c")
    group = only_kind(resolved, "moMateGroup_c")
    explode = RequireNode(root.FieldsValue.get("f1590"), "moExplViewManager_c")
    children, notes = ReadChildren(env), ReadChildren(cabinet)
    require(root.FieldsValue["f1e0"] is env
            and root.FieldsValue.get("f1598") == 0
            and tuple(row.ClassValue.NameValue for row in children)
            == ("moAmbientLight_c", "moDirectionLight_c", "moDirectionLight_c", "moDirectionLight_c")
            and tuple(row.ClassValue.NameValue for row in notes) == ("moNotesAreaFtrFolder_c",) * 2
            and all(ref.ClassValue.NameValue == "moReference_c" for ref in refs)
            and mates[0].ClassValue.NameValue == "moMateConcentric"
            and not ReadChildren(group) and not group.FieldsValue["f4e8"],
            "chronology requires the actual ordinary environment, cabinet, exploded and mate group owners")
    entries = {MODEL: root}
    for scope, rows, parent in (
        ("resolved", resolved, root), ("light", children, env), ("note", notes, cabinet),
        ("exploded", (explode,), root), ("occurrence", refs, root), ("mate", mates, group),
    ):
        for row in rows:
            kind = row.ClassValue.NameValue
            role = (scope, kind, AsmKeywordName(row))
            require(row.ClassValue == RuntimeClass(kind, 1)
                    and role not in entries and (not constructed or row.FieldsValue.get("owner") is parent),
                    "chronology feature is ambiguous or detached from its actual owner")
            entries[role] = row
    by_id = {FieldInt(row.FieldsValue, "f08"): role for role, row in entries.items()}
    require(len(by_id) == len(entries) == 27 and by_id.get(0) == MODEL
            and all(0 <= key <= 0x7FFFFFFF for key in by_id) and EXPLODED in entries,
            "chronology requires distinct live model and feature persistent identities")
    return entries


def wide_text(value):
    require(type(value) is CStringValue and value.IsUnicode, "chronology requires own typed wide text")
    return value.TextValue


def attribution_table(node):
    require(RequireNode(node, "su_CStringArray").ClassValue == RuntimeClass("su_CStringArray", 0),
            "chronology requires the ordinary attribution table schema")
    return tuple(wide_text(text) for text in node.FieldsValue["values"])


def clocks(header):
    fields = header.FieldsValue
    return HeaderClocks(FieldInt(fields, "f70"), FieldInt(fields, "f50"), FieldInt(fields, "f48"))


def read_book(header, owning_nodes):
    fields = header.FieldsValue
    users, companies = (attribution_table(fields[key]) for key in ("f10", "f18"))
    keys = {FieldInt(row.FieldsValue, "f08"): role for role, row in owning_nodes.items()}
    events = []
    for row in ReadLogItems(fields["f20"], "moLogs_c"):
        key = FieldInt(row.FieldsValue, "f48")
        require(key in keys, "revision log has no live assembly owner")
        values = []
        for stamp in ReadLogItems(row, "moStamp_c"):
            event = stamp.FieldsValue
            mode, user, company = (FieldInt(event, field) for field in ("f08", "f0c", "f10"))
            require(mode in EVENT_OPS and 0 <= user < len(users) and 0 <= company < len(companies),
                    "revision event operation or attribution is outside the observed scope")
            values.append(asdict(RevisionEvent(EVENT_OPS[mode], users[user], companies[company],
                                                FieldInt(event, "f18"), wide_text(event["f20"]))))
        events.append({"role": keys[key], "caption": wide_text(row.FieldsValue["f50"]), "events": values})
    return {"users": users, "companies": companies, "logs": events}


def read_instants(owning_nodes):
    return [{"role": role, "instant": asdict(ReadMemberTime(row))}
            for role, row in owning_nodes.items() if role != MODEL]


def role_key(table, key, message):
    require(isinstance(key, (tuple, list)) and len(key) == 3 and all(type(value) is str for value in key)
            and tuple(key) in table, message)
    return tuple(key)


def make_book(owning_nodes, intent):
    require(set(intent) == {"users", "companies", "logs"}, "revision needs only typed attribution and log intent")
    available = set(owning_nodes) - {EXPLODED}
    logs = []
    for record in intent["logs"]:
        require(set(record) == {"role", "caption", "events"}, "revision log intent has an unknown field")
        role = role_key(available, record["role"], "revision log owner is missing, foreign or duplicated")
        available.remove(role)
        events = tuple(RevisionEvent(**row) for row in record["events"])
        require(1 <= len(events) <= 2 and events[0].OperationValue == "created"
                and (len(events) == 1 or (events[1].OperationValue == "modified"
                                         and events[0].EventAt <= events[1].EventAt)),
                "revision log does not retain the measured creation/modification order")
        logs.append(RevisionLog(owning_nodes[role], record["caption"], events))
    require(not available and logs[0].OwnerValue is owning_nodes[MODEL],
            "revision log inventory omits an actual owner or displaces the root")
    return RevisionBook(tuple(intent["users"]), tuple(intent["companies"]), tuple(logs))


def make_instants(owning_nodes, rows):
    available = set(owning_nodes) - {MODEL}
    result = []
    for row in rows:
        require(set(row) == {"role", "instant"}, "feature instant intent has an unknown field")
        role = role_key(available, row["role"], "feature instant owner is missing, foreign or duplicated")
        available.remove(role)
        result.append((owning_nodes[role], MakeFeatTime(FeatureInstant(**row["instant"]))))
    require(not available, "feature instant inventory omits an actual feature owner")
    return result


def revision_fields(book):
    graph = MakeRevBook(book)
    return {"f10": graph.UsersValue, "f18": graph.CompaniesValue, "f20": graph.LogsValue}


def header_seed(intent, current_save):
    time = HeaderClocks(**intent["header"])
    root = intent["book"]["logs"][0]
    event = RevisionEvent(**root["events"][0])
    require(tuple(root["role"]) == MODEL and event.OperationValue == "created"
            and event.EventAt <= time.CreatedAt <= time.UpdatedAt <= current_save
            and time.ArchiveAt <= current_save,
            "assembly header and current save must join the actual initial model event")
    return HeaderInput(event.UserName, event.CompanyName, event.CommentText, time.CreatedAt,
                       max(time.CreatedAt, time.ArchiveAt), time.UpdatedAt)


def attach_intent(bundle, intent):
    time = HeaderClocks(**intent["header"])
    nodes = owners(bundle.StateValue.RootValue, bundle.StateValue.FeatureValues, bundle.OccurrenceValues,
                   bundle.MateValues, constructed=True)
    book = make_book(nodes, intent["book"])
    instants = make_instants(nodes, intent["features"])
    headers = bundle.HeaderValue, bundle.TopHeader
    self_records = tuple(node.FieldsValue["f38"] for node in headers)
    require(headers[0] is not headers[1] and self_records[0] is self_records[1]
            and self_records[0].FieldsValue["shared"]["f28"] == time.CreatedAt
            and all(node.FieldsValue["f70"] == time.CreatedAt and node.FieldsValue["f48"] == time.UpdatedAt
                    for node in headers),
            "chronology requires the actual paired generated headers and their shared creation owner")
    for header in headers:
        header.FieldsValue.update(revision_fields(book), f50=time.ArchiveAt)
    for node, words in instants:
        node.FieldsValue.update(words)
