from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import MakeBiography
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import MakeFreshHist
from convert.adapters.solidworks.Archive.History.ReadHistGraph import ReadHistGraph
from convert.adapters.solidworks.Archive.History.WriteHistGraph import WriteHistGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

VERSION = 19000
PREFIX = "_MO_VERSION_19000/"
MANIFEST = ROOT / "re/solidworks/measurements/2026/HistoryStreamSources01.json"
CASES = ("ladder", "annulus", "concave", "authored", "edited")


def require(valid, message):
    if not valid:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def load_control(case):
    manifest = json.loads(MANIFEST.read_bytes())
    expected = manifest["controls"][case]
    source = ROOT / expected["path"]
    require(source.is_file() and not source.is_symlink(), "native control must be its disclosed file")
    payload = source.read_bytes()
    require(digest(payload) == expected["sha256"] and len(payload) == expected["bytes"],
            "disclosed history control changed")
    archive = SldprtArchive.from_bytes(payload)
    require(archive.format_version == manifest["physical_format"] == 4
            and ContainerMo(archive.streams) == manifest["archive_version"] == VERSION,
            "disclosed history control changed version")
    return {name: archive.require(PREFIX + name) for name in expected["streams"]}, expected


def describe(graph, data, role):
    root = graph.RootValue
    fields = root.FieldsValue
    entries = graph.MapValue.EntriesValue
    require(graph.ReportValue["completed"] and root.StartOffset == 0 and root.EndOffset == len(data)
            and entries[1].EntryValue is root and entries[0].EntryValue is root.ClassValue,
            "standalone history did not consume its exact root and map")
    members = []
    for entry in entries:
        value = entry.EntryValue
        class_value = value.ClassValue if isinstance(value, ArchiveNode) else value
        members.append([entry.IndexValue, type(value).__name__, class_value.NameValue])
    result = {"bytes": len(data), "counter": graph.MapValue.CounterValue, "map": members,
              "n": fields["n"], "sha256": digest(data)}
    if role == "History":
        children = [row["st"]["f38"] for row in fields["states"]]
        require(entries[3].EntryValue is children[0] and entries[2].EntryValue is children[0].ClassValue,
                "the stored date history did not bind its actual class and object")
        result.update(version=[row["st"]["f30"] for row in fields["states"]],
                      date_counts=[child.FieldsValue["n"] for child in children])
    return result


def verify_control(streams, control):
    reports = {}
    for role, data in streams.items():
        graph = ReadHistGraph(data, VERSION)
        expected = control["streams"][role]
        report = describe(graph, data, role)
        require(report == expected, f"{role} physical bytes or map differ")
        output, reissued = WriteHistGraph(graph.RootValue, VERSION)
        require(output == data and reissued.RootValue is not graph.RootValue
                and describe(reissued, output, role) == report,
                f"{role} typed re-emission changed bytes or output map")
        reports[role] = report | {"exact_reemission": True}
    return {"source_sha256": control["sha256"], "streams": reports}


def new_class(name):
    label = name.encode("ascii")
    return pack("<HHH", 0xffff, 1, len(label)) + label


def version_stamp(created, comment):
    text = comment.encode("utf-16-le")
    units = len(text) // 2
    require(units < 255, "authored wire uses the ordinary one byte length")
    return pack("<HHHI", 0, 0, 0, created) + b"\xff\xfe\xff" + bytes((units,)) + text


def history_tail(spec):
    return pack("<iIiHii", 0, 0xffffffff, spec.LicenseOrigin, spec.LanguageId, spec.CjkSaved, 0)


def history_wire(spec):
    stamp = version_stamp(spec.CreatedAt, spec.CommentText)
    date = new_class("moDateCodeHistory_c") + pack("<ii", 1, spec.BuildCode)
    return (new_class("moVersionHistory_c") + pack("<i", 1)
            + stamp + pack("<I", VERSION) + date + history_tail(spec))


def check_emitted(root, expected):
    actual, graph = WriteHistGraph(root, VERSION)
    require(actual == expected and graph.RootValue is not root and graph.ReportValue["completed"],
            "generated history differs from the independently framed record")
    return graph


def history_spans(spec, data):
    date_start = len(new_class("moVersionHistory_c")) + 4 + len(version_stamp(spec.CreatedAt, spec.CommentText)) + 4
    return [[0, len(data)], [date_start, len(data) - len(history_tail(spec))]]


def edited():
    original = HistoryInput(1881802743, "short", 2031447, 0, 1033, False)
    revised = replace(original, CommentText="longer \U0001d11e comment")
    source = history_wire(original)
    source_graph = ReadHistGraph(source, VERSION)
    root = source_graph.RootValue
    state = root.FieldsValue["states"][0]["st"]
    date = state["f38"]
    state["f08"]["f20"] = revised.CommentText
    output, emitted_graph = WriteHistGraph(root, VERSION)
    emitted_root = emitted_graph.RootValue
    emitted_state = emitted_root.FieldsValue["states"][0]["st"]
    emitted_date = emitted_state["f38"]
    source_spans = [[node.StartOffset, node.EndOffset] for node in (root, date)]
    emitted_spans = [[node.StartOffset, node.EndOffset] for node in (emitted_root, emitted_date)]
    require(output == history_wire(revised) and emitted_state["f08"]["f20"] == revised.CommentText,
            "comment edit did not emit the independent longer wire")
    require(source_spans == history_spans(original, source) and state["f38"] is date
            and source_graph.MapValue.EntriesValue[3].EntryValue is date,
            "history emission changed source coordinate or owner identity")
    require(emitted_spans == history_spans(revised, output)
            and emitted_root is not root and emitted_date is not date
            and date.IndexValue == emitted_date.IndexValue == 4,
            "history emission returned stale coordinates or the wrong map owner")
    describe(emitted_graph, output, "History")
    return {"source_spans": source_spans, "emitted_spans": emitted_spans,
            "date_slot": emitted_date.IndexValue, "source_sha256": digest(source),
            "output_sha256": digest(output)}


def fresh_history(spec):
    root = MakeFreshHist(spec)
    expected = history_wire(spec)
    graph = check_emitted(root, expected)
    status = describe(graph, expected, "History")
    fields = graph.RootValue.FieldsValue
    state = fields["states"][0]["st"]
    date = state["f38"].FieldsValue["states"][0]["st"]["f08"]
    require((state["f08"]["f18"], state["f08"]["f20"], date, fields["f30"], fields["f38"], fields["f3c"])
            == (spec.CreatedAt, spec.CommentText, spec.BuildCode, spec.LicenseOrigin, spec.LanguageId, spec.CjkSaved),
            "generated source semantics differ from the explicit provenance")
    return status | {"created": spec.CreatedAt, "date_code": date, "comment": spec.CommentText,
                     "license_origin": fields["f30"], "language": fields["f38"], "cjk_saved": fields["f3c"]}


def shared_date_history(spec, next_spec):
    root = MakeFreshHist(spec)
    rows = root.FieldsValue["states"]
    second_stamp = {**rows[0]["st"]["f08"], "f18": next_spec.CreatedAt, "f20": next_spec.CommentText}
    rows.append({"st": {**rows[0]["st"], "f08": second_stamp}})
    root.FieldsValue["n"] = 9
    first_wire = history_wire(spec)
    root_tag = new_class("moVersionHistory_c")
    tail = history_tail(spec)
    expected = (root_tag + pack("<i", 2) + first_wire[len(root_tag)+4:-len(tail)]
                + version_stamp(next_spec.CreatedAt, next_spec.CommentText) + pack("<IH", VERSION, 4) + tail)
    graph = check_emitted(root, expected)
    fields = graph.RootValue.FieldsValue
    owner, repeated = (row["st"]["f38"] for row in fields["states"])
    require(owner is repeated and owner.IndexValue == 4 and fields["n"] == 2
            and root.FieldsValue["n"] == 9, "shared date history or derived count changed")
    return {"counter": graph.MapValue.CounterValue, "date_slot": owner.IndexValue, "count": fields["n"],
            "authored_count_preserved": root.FieldsValue["n"], "sha256": digest(expected)}


def refuse(label, action, reason):
    try:
        action()
    except ValueError as error:
        require(reason in str(error), f"{label} refused for a different reason: {error}")
        return label
    raise ValueError(f"{label} accepted an unsupported history")


def read_refusals(spec):
    version_tag = new_class("moVersionHistory_c")
    date_tag = new_class("moDateCodeHistory_c")
    bio_tag = new_class("moBiography_c")
    prefix = version_tag + pack("<i", 1) + version_stamp(spec.CreatedAt, spec.CommentText)
    state = prefix + pack("<I", VERSION)
    wires = (
        ("negative_biography_count", bio_tag + pack("<i", -1), "implausible SOLIDWORKS body repeat"),
        ("truncated_biography_row", bio_tag + pack("<i", 1), "truncated SOLIDWORKS archive field"),
        ("empty_version_history", version_tag + pack("<i", 0), "version history requires states"),
        ("wrong_inner_version", prefix + pack("<I", 18999), "history state requires version 19000"),
        ("wrong_root_owner", date_tag, "unsupported object role"),
        ("wrong_date_owner", state + bio_tag, "unsupported object role"),
        ("null_date_history", state + pack("<H", 0) + history_tail(spec), "requires date code history"),
        ("wrong_date_alias", state + pack("<H", 2) + history_tail(spec), "requires date code history"),
        ("empty_date_history", state + date_tag + pack("<i", 0), "date code history requires states"),
        ("trailing_bytes", history_wire(spec) + b"\0", "history stream has trailing data"),
    )
    reports = [refuse(name, lambda: ReadHistGraph(wire, VERSION), diagnostic) for name, wire, diagnostic in wires]
    reports.append(refuse("wrong_outer_version", lambda: ReadHistGraph(history_wire(spec), 18900),
                          "history requires archive version 19000"))
    return reports


def authored():
    first = HistoryInput(1881802743, "authored λ", 2031447, 0, 1033, False)
    second = HistoryInput(1909975145, "independent \U0001d11e", 2040693, 30, 1041, True)
    empty_wire = new_class("moBiography_c") + pack("<i", 0)
    empty = describe(check_emitted(MakeBiography(), empty_wire), empty_wire, "Biography")
    malformed = MakeFreshHist(first)
    malformed.FieldsValue["states"][0]["st"]["f38"] = MakeBiography()
    negative_write = refuse("wrong_authored_date_owner", lambda: WriteHistGraph(malformed, VERSION),
                            "requires date code history")
    return {"fresh_biography": empty, "fresh_histories": [fresh_history(first), fresh_history(second)],
            "aliased_date_history": shared_date_history(first, second),
            "refusals": [*read_refusals(first), negative_write]}


def main():
    parser = ArgumentParser(description="Check the ordinary version 19000 History and Biography streams")
    parser.add_argument("case", choices=CASES)
    case = parser.parse_args().case
    control = load_control(case) if case in ("ladder", "annulus", "concave") else None
    for encoding in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)
    sys.addaudithook(audit_run)
    if control is not None:
        result = verify_control(*control)
    else:
        result = authored() if case == "authored" else edited()
    print(json.dumps(result | {"case": case, "runtime_external_accesses": 0}, sort_keys=True, ensure_ascii=True))


if __name__ == "__main__":
    main()
