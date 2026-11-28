from argparse import ArgumentParser
from ast import Import, ImportFrom, parse, walk
from collections import Counter, deque, defaultdict
from hashlib import sha256
from importlib.util import resolve_name
from pathlib import Path
from subprocess import Popen, PIPE, check_output
import json
import sys

parser = ArgumentParser(description="Count static writer dependencies at pinned Git revisions")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[3]
main = "c1809221c0910c301dd457ce92e51e7b1b74f522"
agg = "df25ff93a08d05ddba0f64e2dd7e5eba82e8bdd2"
early = "81aff00e947ef3bb39fb479c265782d7ca7a0581"
box = "93c0174353bdc7a4cd3dd155b2ba40066ac96483"

def git(*args):
    return check_output(("git", *args), cwd=root)

def tracked(revision):
    items = {}
    for row in git("ls-tree", "-rz", revision, "src").split(b"\0"):
        if not row:
            continue
        header, path = row.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        if kind == "blob":
            items[path.decode()] = oid
    return items

def mod_name(path):
    name = path.removeprefix("src/").removesuffix(".py")
    return name.removesuffix("/__init__").replace("/", ".")

def module_sources(entries):
    files, payloads = {}, {}
    with Popen(("git", "cat-file", "--batch"), stdin=PIPE, stdout=PIPE, cwd=root) as stream:
        for path, oid in entries.items():
            if not path.endswith(".py"):
                continue
            stream.stdin.write((oid + "\n").encode())
            stream.stdin.flush()
            got, kind, size = stream.stdout.readline().decode().split()
            assert got == oid and kind == "blob"
            data = stream.stdout.read(int(size))
            assert stream.stdout.read(1) == b"\n"
            files[mod_name(path)] = path
            payloads[path] = data
    return files, payloads

def import_edges(files, payloads):
    edges = defaultdict(set)
    for module, path in files.items():
        package = module if path.endswith("/__init__.py") else module.rpartition(".")[0]
        target = edges[module]
        syntax = parse(payloads[path], filename=path)
        for statement in walk(syntax):
            if isinstance(statement, Import):
                target.update(alias.name for alias in statement.names)
            elif isinstance(statement, ImportFrom):
                origin = statement.module or ""
                if statement.level:
                    origin = resolve_name("." * statement.level + origin, package)
                target.add(origin)
                target.update(f"{origin}.{alias.name}" for alias in statement.names)
        target.intersection_update(files)
        target.discard(module)
    return edges

def reach(starts, files, edges, parents):
    pending = deque(starts)
    visited = set()
    while pending:
        value = pending.popleft()
        if value in visited:
            continue
        assert value in files, value
        visited.add(value)
        pending.extend(edges.get(value, ()))
        if parents:
            segments = value.split(".")
            prefixes = [".".join(segments[:i]) for i in range(1, len(segments))]
            pending.extend(item for item in prefixes if item in files)
    return {files[module] for module in visited}

def changed_counts(base, revision):
    deltas = {}
    for item in git("diff", "--no-renames", "--numstat", "-z", base, revision, "--", "src").split(b"\0"):
        if item:
            plus, minus, path = item.split(b"\t", 2)
            deltas[path.decode()] = None if plus == b"-" else [int(plus), int(minus)]
    return deltas

def view(paths, entries, origin_files, payloads, deltas):
    missing = sorted(item for item in paths if item not in origin_files)
    differing = sorted(item for item in paths if item in origin_files and origin_files[item] != entries[item])
    info = {}
    for label, items in (("missing", missing), ("different", differing)):
        info[label] = [
            {"path": item, "git_blob": entries[item], "sha256": sha256(payloads[item]).hexdigest(),
             "bytes": len(payloads[item]), "lines": len(payloads[item].splitlines()),
             "direct_diff_lines": deltas[item]}
            for item in items
        ]
    absent = missing + differing
    group = Counter()
    for item in absent:
        pieces = item.split("/")
        if item.startswith("src/convert/adapters/solidworks/"):
            group["/".join(pieces[4:(7 if len(pieces) >= 8 else 6)])] += 1
        else:
            group["/".join(pieces[1:4])] += 1
    return {
        "closure_count": len(paths), "missing_count": len(missing), "different_count": len(differing),
        "unchanged_count": len(paths) - len(absent), "direct_diff_additions": sum(deltas[x][0] for x in absent),
        "direct_diff_deletions": sum(deltas[x][1] for x in absent),
        "missing_plus_changed_bytes": sum(len(payloads[x]) for x in absent),
        "groups": sorted(group.items(), key=lambda x: (-x[1], x[0])),
        "paths": sorted(paths),
        **info,
    }

base = tracked(main)
archive = "convert.adapters.solidworks.Archive."
body = archive + "Bodies."
core = "convert.adapters.solidworks.Core."
prep = core + "Preparation."
plan = (prep + "PlanPartWrite", prep + "MakePartRecipe", prep + "RunPartPrep", prep + "CheckPartOpts",
        "convert.adapters.solidworks.Container.Container")
routes = {
    "plainLineBossSelected": plan,
    "circleSelected": (prep+"Circle.PlanCircle", prep+"Circle.PrepareCircle", prep+"CheckPartOpts",
                       "convert.adapters.solidworks.Container.Container"),
    "plainBrepSelected": (prep+"Imports.PlanImportPart", prep+"Imports.PrepareImport", prep+"CheckPartOpts"),
    "sharedPartArchive": (archive+"Construction.Part.EmitPartArchive",),
    "historyMetadata": (archive+"Construction.Metadata.MakeBiography", archive+"Construction.Metadata.MakeFreshHist",
                        archive+"History.WriteHistMut", archive+"History.ReadHistMut"),
    "historyDirectCandidate": (archive+"Construction.Metadata.MakeBiography", archive+"Construction.Metadata.MakeFreshHist",
                        archive+"History.WriteHistMut", archive+"History.ReadHistMut"),
    "atomWriterInputs": (archive+"Construction.BodyNames.MakeColdAtom",
                         archive+"Construction.BodyScope.MakeStockAtom",
                         archive+"Construction.Part.Imports.BindImportMut",
                         archive+"Bodies.Layouts.Config.AtomFields"),
    "registry": (core+"Writing.SldprtWriter", "convert.api.ApiWrite"),
    "definition": (archive+"Definition.Construction.MakePartDef", archive+"Definition.WriteModelDef"),
    "cmgr": (archive+"Cmgr.WriteCmgrMut",),
    "resolved": (archive+"Resolved.WriteResolMut",),
    "config": (archive+"Config.WriteConfigMut",),
    "publicPartCore": (core+"Writing.EmitNativeMut", core+"Writing.PartWriteInfo"),
    "bodyWriteMinMainDelta": (archive+"Bodies.WriteBodyMut",),
}

tests = {}
for revision, key, included in (
    (agg,"aggregate",set(routes)),
    (early,"line-native-equivalent",{"plainLineBossSelected","registry","historyMetadata"}),
    (box,"box-native-exact",{"plainLineBossSelected","plainBrepSelected","registry","atomWriterInputs"}),
):
    entries = tracked(revision)
    files, payloads = module_sources(entries)
    edges = import_edges(files, payloads)
    deltas = changed_counts(main, revision)
    measured = {}
    for label, starts in routes.items():
        if label not in included:
            continue
        if not all(item in files for item in starts):
            print(key, label, "missing start", [item for item in starts if item not in files])
            continue
        if label == "historyDirectCandidate":
            main_edges = dict(edges)
            for name in (body+"IsBranchTaken", body+"Writing.WriteActions", body+"Reading.ReadActions",
                         body+"Writing.WriteNestedMut"):
                if name in edges:
                    main_edges[name] = frozenset(e for e in edges[name] if files[e] in base)
            view_paths = reach(starts,files,main_edges,False)
        else:
            view_paths = reach(starts,files,edges,label=="registry")
        measured[label] = view(view_paths, entries, base, payloads, deltas)
        for field in ("missing_count", "different_count", "direct_diff_additions", "direct_diff_deletions", "closure_count"):
            print(measured[label][field], end=" ")
        print(key, label)
    tests[key] = measured
print("wrote report")
args.output.write_text(json.dumps({"accepted_base":main, "aggregate":agg, "historical_line":early,
    "historical_box":box, "measurements":tests}, indent=2, sort_keys=True)+"\n", encoding="utf-8")
