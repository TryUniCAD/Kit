from argparse import ArgumentParser
from codecs import lookup
from pathlib import Path
from subprocess import check_output
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "re/automation"), str(ROOT / "re/solidworks/EncoderBoundary")]

from EncoderRoundTrip.Artifacts import NATIVE_LIMIT, canonical_json, digest, read_record, write_artifact
from InspectVendorBodyOwners import REVISION, verify_dependency

ORDINARY_REVISION = "0d1f6633e6e9e834a200d3c02990b3dea3174c9b"
SCHEMA = "kit.research.resaved-renderer-read.v1"


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def verify_ordinary(root):
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=root).decode().strip()
    changed = check_output(("git", "status", "--porcelain", "--untracked-files=no"), cwd=root)
    demand(revision == ORDINARY_REVISION and not changed, "ordinary reader requires the unmodified pinned PR316 checkout")


def read_inputs(path):
    raw = path.read_bytes()
    manifest = read_record(raw)
    demand(set(manifest) == {"schema", "cases"} and manifest["schema"] == SCHEMA, "expected the private renderer input manifest")
    cases = manifest["cases"]
    demand(type(cases) is list and 1 <= len(cases) <= 16, "expected one to sixteen disclosed cases")
    names = set()
    for row in cases:
        demand(type(row) is dict and set(row) == {"name", "path", "sha256"}, "unexpected input custody fields")
        name = row["name"]
        demand(type(name) is str and name.isascii() and name.isalnum() and name not in names, "input labels must be unique ASCII identifiers")
        names.add(name)
        source = Path(row["path"])
        expected = row["sha256"]
        demand(source.is_absolute() and source.suffix.casefold() == ".sldprt", "input requires an absolute disclosed part path")
        demand(type(expected) is str and len(expected) == 64 and all(c in "0123456789abcdef" for c in expected), "input requires its lowercase SHA256")
        demand(source.stat().st_size <= NATIVE_LIMIT and digest(source.read_bytes()) == expected, "input differs from its bound native digest")
    return raw, cases


def map_rows(snapshot):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

    return [
        {"slot": entry.IndexValue, "kind": "object" if isinstance(entry.EntryValue, ArchiveNode) else "class",
         "class": (entry.EntryValue.ClassValue if isinstance(entry.EntryValue, ArchiveNode) else entry.EntryValue).NameValue,
         "schema": (entry.EntryValue.ClassValue if isinstance(entry.EntryValue, ArchiveNode) else entry.EntryValue).SchemaValue}
        for entry in snapshot.EntriesValue
    ]


def same_map(before, after):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

    demand(before.CounterValue == after.CounterValue and map_rows(before) == map_rows(after), "Definition map allocation changed")
    for first, second in zip(before.EntriesValue, after.EntriesValue, strict=True):
        a, b = first.EntryValue, second.EntryValue
        demand(a is b if isinstance(a, ArchiveNode) else a == b, "Definition map owner identity changed")


def guarded(action):
    active, attempts = True, []

    def audit(event, _):
        if active and (event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.spawn", "os.startfile", "os.fork", "os.posix_spawn", "os.forkpty")
                       or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))):
            attempts.append(event)
            raise RuntimeError("external access during in-memory Definition inspection")

    sys.addaudithook(audit)
    try:
        result = action()
    finally:
        active = False
    demand(not attempts, "Definition inspection crossed its input boundary")
    return result


def worker(args):
    if args.mode in ("general", "ordinary"):
        verify_dependency(args.reader_root)
    else:
        verify_ordinary(args.reader_root)
    sys.path.insert(0, str(args.reader_root / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    demand(Path(ReadModelDef.__code__.co_filename).resolve().is_relative_to(args.reader_root.resolve() / "src"), "reader import escaped its pinned checkout")

    if args.mode == "general":
        from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyAppr import ReadEmptyAppr
        from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeAppearMgr import MakeAppearMgr

    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)

    _, cases = read_inputs(args.manifest)
    outcomes = {}
    for row in cases:
        source = Path(row["path"])
        raw = source.read_bytes()
        demand(digest(raw) == row["sha256"], "native input changed before inspection")
        archive = SldprtArchive.from_bytes(raw, "<disclosed renderer inspection>")
        demand(ContainerMo(archive.streams) == 19000, "input requires the measured version19000 archive")
        data = archive.Require("Contents/Definition")
        if args.mode == "public":
            try:
                document = open_document(raw, source_format="solidworks.sldprt", strict=True)
                by_id = {feature.id: feature for feature in document.feature_timeline}
                drivers = []
                for parameter in document.parameters:
                    if parameter.name != "D1":
                        continue
                    feature = by_id.get(parameter.owner_id)
                    native_value = parameter.attributes.get("native_value")
                    drivers.append({"owner_id": parameter.owner_id, "role": str(parameter.role),
                                    "value": parameter.value.value, "unit": parameter.value.unit,
                                    "retained_native_si_word": native_value.hex() if type(native_value) is float else None,
                                    "linked_feature_length_matches": feature is not None and getattr(feature.definition, "length", None) == parameter.value})
                result = {"status": "returned_document", "diagnostic_origin": "PR316 open_document(strict=True)",
                          "diagnostics": [{"code": d.code, "message": d.message, "severity": str(d.severity), "entity_id": d.entity_id} for d in document.diagnostics],
                          "configuration_names": [configuration.name for configuration in document.configurations], "d1": drivers,
                          "sketches": len(document.sketches), "parameters": len(document.parameters), "bodies": len(document.bodies)}
            except (ValueError, TypeError, KeyError) as error:
                result = {"status": "refused", "type": type(error).__name__, "message": str(error)}
        else:
            def inspect():
                if args.mode == "ordinary":
                    ReadModelDef(data, 19000, OrdinaryOnly=True)
                    return {"status": "admitted"}
                if args.mode == "frozen":
                    ReadModelDef(data, 19000)
                    return {"status": "admitted"}
                read = ReadModelDef(data, 19000)
                fields = read.GraphValue.DocumentValue.FieldsValue
                owner = ReadEmptyAppr(fields)
                predicted = MakeAppearMgr(owner)
                demand(predicted == {key: fields[key] for key in predicted}, "empty appearance owner did not re-emit exactly")
                written = WriteModelDef(read.GraphValue)
                demand(written.OutputValue == data, "general Definition re-emission differs")
                same_map(read.MapValue, written.MapValue)
                return {"status": "exact_codec_replay", "class": read.GraphValue.DocumentValue.ClassValue.NameValue,
                        "version": 19000, "definition_bytes": len(data), "definition_sha256": digest(data),
                        "manager_on_wire": owner.ManagerOnWire, "next_appearance_id": owner.NextAppearanceId,
                        "signed_counter_words": None if not owner.ManagerOnWire else [fields["f1110"]["f08"], fields["f1110"]["f0c"]],
                        "reference_count": None if not owner.ManagerOnWire else fields["f1110"]["list"]["n"],
                        "map_next": read.MapValue.CounterValue, "map_sha256": digest(canonical_json(map_rows(read.MapValue))),
                        "exact_owner_reemit": True, "exact_definition_reemit": True, "exact_map_identity": True}

            try:
                result = guarded(inspect)
            except (ValueError, TypeError, KeyError) as error:
                if args.mode == "general":
                    raise
                result = {"status": "refused", "type": type(error).__name__, "message": str(error)}
        demand(digest(source.read_bytes()) == row["sha256"], "native input changed during inspection")
        outcomes[row["name"]] = result
    return outcomes


def run(args):
    verify_ordinary(args.ordinary_root)
    verify_dependency(args.dependency_root)
    demand(not args.output.exists(), "renderer inspection requires a fresh output directory")
    manifest, cases = read_inputs(args.manifest)
    results = {}
    for mode in ("general", "ordinary", "frozen", "public"):
        root = args.dependency_root if mode in ("general", "ordinary") else args.ordinary_root
        raw = check_output((sys.executable, "-I", "-B", str(Path(__file__).resolve()), "worker", "--manifest", str(args.manifest),
                            "--reader-root", str(root), "--mode", mode))
        results[mode] = read_record(raw)
    demand(args.manifest.read_bytes() == manifest, "private input manifest changed")
    verify_ordinary(args.ordinary_root)
    verify_dependency(args.dependency_root)
    for row in cases:
        demand(digest(Path(row["path"]).read_bytes()) == row["sha256"], "native input custody changed")
    report = {"schema": SCHEMA, "stage": "offline_codec_and_scope_diagnosis", "tool_sha256": digest(Path(__file__).read_bytes()),
              "private_manifest_sha256": digest(manifest), "general_reader_revision": REVISION, "ordinary_reader_revision": ORDINARY_REVISION,
              "scope": "Exact existing Definition codec and retained ordinary/public outcomes; no new admission or native acceptance",
              "native_launches": 0, "cases": {
                  row["name"]: {"archive_sha256": row["sha256"], **{mode: results[mode][row["name"]] for mode in results}}
                  for row in cases}}
    args.output.mkdir()
    write_artifact(args.output, "Report.json", canonical_json(report))
    return report


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect disclosed resaved Definition appearance owners without relaxing ordinary admission")
    commands = parser.add_subparsers(dest="command", required=True)
    measure = commands.add_parser("inspect")
    for name in ("manifest", "dependency-root", "ordinary-root", "output"):
        measure.add_argument("--" + name, type=Path, required=True)
    child = commands.add_parser("worker")
    child.add_argument("--manifest", type=Path, required=True)
    child.add_argument("--reader-root", type=Path, required=True)
    child.add_argument("--mode", choices=("general", "ordinary", "frozen", "public"), required=True)
    args = parser.parse_args()
    sys.stdout.buffer.write(canonical_json(run(args) if args.command == "inspect" else worker(args)))
