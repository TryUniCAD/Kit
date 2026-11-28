from argparse import ArgumentParser
from codecs import lookup
from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
from stat import S_ISLNK
from struct import pack
from subprocess import check_output, run
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile


HERE = Path(__file__).resolve()
PROFILE = "re/solidworks/measurements/2026/HistoryHeldoutProtocol01.json"
TOOL = "re/tooling/sw2026/VerifyHeldoutHistory.py"
PACKET = "kit.sw2026.standalone-history-heldout-packet.v1"
RECEIPT = "kit.sw2026.standalone-history-heldout-result.v1"
INPUTS = ("Protocol.json", "Source.zip", HERE.name)
VERSION = 19000
PREFIX = "_MO_VERSION_19000/"
ROOTS = {"Biography": "moBiography_c", "History": "moVersionHistory_c"}
IO_EVENTS = {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork", "os.forkpty",
             "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen", "socket.connect"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encode(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "expected an ordinary pinned file")
    data = path.read_bytes()
    require(digest(data) == expected, "pinned file identity differs")
    return data


def git(*args):
    return check_output(("git", *args), cwd=HERE.parents[3])


def object_bytes(revision, path):
    return git("cat-file", "blob", revision + ":" + path)


def verify_authority(profile):
    revision = profile["authority_revision"]
    lock = profile["polygon_source_lock"]
    native = profile["previous_native_source_replay"]
    first = profile["first_form_rules"]
    lock_bytes = object_bytes(lock["lock_commit"], lock["path"])
    native_bytes = object_bytes(revision, native["path"])
    require(digest(lock_bytes) == lock["sha256"] and digest(native_bytes) == native["sha256"],
            "historical source or native receipt pin differs")
    source = json.loads(lock_bytes)
    observed = json.loads(native_bytes)
    locked = datetime.fromisoformat(source["locked_at_utc"])
    first_code = datetime.fromisoformat(git("show", "-s", "--format=%aI",
                                            first["first_donor_free_model_constructor"]).decode().strip())
    require(source["baseline_head"] == lock["baseline"] and locked < first_code
            and locked == datetime.fromisoformat(lock["locked_at_utc"])
            and first_code == datetime.fromisoformat(first["first_donor_free_model_constructor_at_utc"]),
            "source lock does not precede the first authored metadata constructor")
    require(observed["source_lock_sha256"] == lock["sha256"] and observed["passed"] is True
            and observed["original_native_inputs_read_by_writer"] == 0
            and observed["original_sources_inspected_after_generation"] == 3
            and observed["oracle"]["file_version"] == native["file_version"]
            and observed["oracle"]["exe_sha256"] == native["executable_sha256"],
            "previous fresh native source authority is incomplete")
    subjects = {row["name"]: row for row in source["records"]}
    replays = {row["slot"]: row for row in observed["cases"]}
    specs = profile["subjects"]
    require(len(specs) == len({row["sha256"] for row in specs}) == 2,
            "must select two distinct locked originals")
    for item in specs:
        saved, replay = subjects[item["basename"]], replays[item["slot"]]
        require(saved["bytes"] == item["bytes"] and saved["sha256"] == item["sha256"]
                and replay["original_source_sha256"] == item["sha256"]
                and replay["source_immutable"] is True and replay["runtime_input_reads"] == 0
                and replay["native_source_tree_equal"] is True and replay["observed"]["native_source"]["body_count"] == 1,
                "native source or prior lifecycle differs")


def stage(revision, directory):
    require(re.fullmatch("[0-9a-f]{40}", revision), "an exact committed revision is required")
    protocol = object_bytes(revision, PROFILE)
    profile = json.loads(protocol)
    verify_authority(profile)
    tree = git("rev-parse", revision + ":src").decode().strip()
    require(tree == profile["codec_src_tree"] == git("rev-parse", profile["codec_revision"] + ":src").decode().strip(),
            "packet must use the pinned PR #206 production tree")
    script = object_bytes(revision, TOOL)
    require(script == HERE.read_bytes(), "running protocol differs from the committed tool")
    files = {"Protocol.json": protocol, HERE.name: script,
             "Source.zip": git("archive", "--format=zip", profile["codec_revision"], "src")}
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        with (directory / name).open("xb") as output:
            output.write(raw)
    packet = encode({"schema": PACKET, "revision": revision, "src_tree": tree,
                     "files": {name: digest(raw) for name, raw in files.items()}})
    with (directory / "Packet.json").open("xb") as output:
        output.write(packet)
    frozen(directory, digest(packet))
    return {"packet_sha256": digest(packet), "src_tree": tree, "source_revision": revision,
            "files": len(files), "protected_payloads_read": 0, "native_processes": 0}


def frozen(directory, pin):
    packet = json.loads(checked(directory / "Packet.json", pin))
    require(packet["schema"] == PACKET and set(packet["files"]) == set(INPUTS)
            and {path.name for path in directory.iterdir()} == {*INPUTS, "Packet.json"},
            "frozen history packet inventory differs")
    files = {name: checked(directory / name, packet["files"][name]) for name in INPUTS}
    profile = json.loads(files["Protocol.json"])
    require(profile["codec_src_tree"] == packet["src_tree"], "frozen profile source tree differs")
    return packet, profile, files["Source.zip"]


def extract(source, work):
    with ZipFile(BytesIO(source)) as archive:
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            require(path.parts[0] == "src" and ".." not in path.parts and "\\" not in member.filename
                    and not S_ISLNK(member.external_attr >> 16),
                    "unexpected frozen SDK archive entry")
        archive.extractall(work)
    return work / "src"


def map_shape(graph, byte_count, role, node_type):
    root = graph.RootValue
    rows = graph.MapValue.EntriesValue
    require(graph.ReportValue["completed"] and root.ClassValue.NameValue == ROOTS[role]
            and root.StartOffset == 0 and root.EndOffset == byte_count
            and tuple(row.IndexValue for row in rows) == tuple(range(1, len(rows) + 1))
            and graph.MapValue.CounterValue == len(rows) + 1
            and rows[0].EntryValue is root.ClassValue and rows[1].EntryValue is root
            and root.IndexValue == 2, "wrong standalone root or archive map")
    members = {row.IndexValue: row.EntryValue for row in rows}
    owners = [root]
    date_counts = []
    if role == "History":
        fields = root.FieldsValue
        states = fields["states"]
        require(len(states) == fields["n"] > 0, "missing standalone version states")
        for state in states:
            version = state["st"]
            owner = version["f38"]
            require(version["f30"] == VERSION and isinstance(owner, node_type)
                    and owner.ClassValue.NameValue == "moDateCodeHistory_c"
                    and members.get(owner.IndexValue) is owner and owner.ClassValue is members.get(3)
                    and 0 < owner.StartOffset < owner.EndOffset <= byte_count,
                    "version state does not bind its real date-code owner")
            date_fields = owner.FieldsValue
            require(len(date_fields["states"]) == date_fields["n"] > 0, "missing standalone date states")
            date_counts.append(date_fields["n"])
            if owner not in owners:
                owners.append(owner)
    else:
        require(len(root.FieldsValue["records"]) == root.FieldsValue["n"] > 0,
                "expected a native populated Biography")
    require({value for value in members.values() if isinstance(value, node_type)} == set(owners),
            "standalone archive contains an unrelated mapped owner")
    identity = tuple((owner.IndexValue, owner.ClassValue.NameValue, owner.StartOffset, owner.EndOffset)
                     for owner in owners)
    return {
        "root_records": root.FieldsValue["n"], "map_counter": graph.MapValue.CounterValue,
        "mapped_nodes": len(owners), "date_record_counts": date_counts, "owner_offsets": identity,
    }, owners


def authored_container(build):
    def tag(name):
        label = name.encode("ascii")
        return pack("<HHH", 0xffff, 1, len(label)) + label

    text = "instrument".encode("utf-16-le")
    stamp = pack("<HHHI", 0, 0, 0, 1810010242) + b"\xff\xfe\xff" + bytes((len(text) // 2,)) + text
    date = tag("moDateCodeHistory_c") + pack("<ii", 1, 2031447)
    history = (tag(ROOTS["History"]) + pack("<i", 1) + stamp + pack("<I", VERSION)
               + date + pack("<iIiHii", 0, 0xffffffff, 0, 1033, 0, 0))
    telemetry = pack("<III", 13, 17, 29) + (b"\xff\xfe\xff\x00" + pack("<iII", 3, 31, 37)) * 6
    bio_record = pack("<Iii6I", VERSION, 2031447, 1, 9, 8, 2, 10, 0, 26100) + b"\xff\xfe\xff\x00" + pack("<H", 1033)
    biography = tag(ROOTS["Biography"]) + pack("<i", 1) + bio_record + telemetry * 2
    return build({PREFIX + "History": history, PREFIX + "Biography": biography}, FormatVersion=4)


def worker(source, authored):
    sys.path.insert(0, str(source))
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from convert.adapters.solidworks.Archive.History.WriteHistGraph import WriteHistGraph
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    raw = authored_container(BuildSldprt) if authored else sys.stdin.buffer.read()
    denied = []

    def guard(event, args):
        if event in IO_EVENTS:
            denied.append(event)
            raise PermissionError("standalone history attempted external access")

    sys.addaudithook(guard)
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
            "wrong native version or physical format")
    result = {}
    for role in ROOTS:
        stream = archive.require(PREFIX + role)
        original = ReadHistMut(stream, VERSION)
        prior, original_owners = map_shape(original, len(stream), role, ArchiveNode)
        emitted, fresh = WriteHistGraph(original.RootValue, VERSION)
        after, new_owners = map_shape(fresh, len(emitted), role, ArchiveNode)
        require(emitted == stream and after == prior
                and not set(original_owners).intersection(new_owners)
                and map_shape(original, len(stream), role, ArchiveNode) == (prior, original_owners),
                "typed stream re-emission did not preserve bytes and archive ownership")
        result[role] = {key: value for key, value in prior.items() if key != "owner_offsets"}
        result[role].update(bytes=len(stream), sha256=digest(stream), exact_reemission=True)
    require(not denied and not {"Swapp", "pythoncom", "win32com"} & sys.modules.keys(),
            "standalone history accessed a native process or runtime file")
    return {"passed": True, "runtime_input_reads": 0, "native_processes_started": 0,
            "file_sha256": digest(raw), "streams": result}


def child(directory, sdk, raw, authored):
    command = (sys.executable, "-I", "-B", str(directory / HERE.name),
               "authored-worker" if authored else "root-worker", str(sdk))
    proc = run(command, input=raw, capture_output=True, timeout=90, check=False)
    require(proc.returncode == 0 and not proc.stderr, "isolated history worker failed")
    result = json.loads(proc.stdout)
    require(result["passed"] is True and result["runtime_input_reads"] == result["native_processes_started"] == 0
            and set(result["streams"]) == set(ROOTS), "isolated history proof incomplete")
    return result


def evaluate(directory, pin, source_root=None):
    packet, profile, source = frozen(directory, pin)
    with TemporaryDirectory(prefix="KitHeldoutHistory.") as name:
        sdk = extract(source, Path(name))
        probe = child(directory, sdk, b"", True)
        if source_root is None:
            return probe | {"protected_payloads_read": 0, "packet_sha256": pin}
        results = []
        for subject in profile["subjects"]:
            path = source_root / subject["basename"]
            require(path.resolve().parent == source_root.resolve() and path.suffix.upper() == ".SLDPRT",
                    "source is not the locked native part")
            payload = checked(path, subject["sha256"])
            require(len(payload) == subject["bytes"], "locked native source length differs")
            observed = child(directory, sdk, payload, False)
            require(observed["file_sha256"] == subject["sha256"] and checked(path, subject["sha256"]) == payload,
                    "original changed during the standalone comparison")
            results.append({"slot": subject["slot"], "source_immutable": True, **observed})
    require(len(results) == 2, "two complete original comparisons are required")
    require(frozen(directory, pin)[0] == packet, "packet changed during protected replay")
    return {"schema": RECEIPT, "passed": True, "packet_sha256": pin, "src_tree": packet["src_tree"],
            "source_revision": packet["revision"], "previous_native_source_replay": profile["previous_native_source_replay"]["sha256"],
            "guard_calibration_sha256": digest(encode(probe)),
            "fresh_codec_processes": len(results), "new_native_processes": 0,
            "qualified_standalone_originals": len(results), "generated_native_document_qualification": False,
            "outputs_containing_source_payloads": 0, "cases": results}


def main():
    parser = ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    prepare = actions.add_parser("stage")
    prepare.add_argument("destination", type=Path)
    prepare.add_argument("--revision", required=True)
    for label in ("verify", "root-replay"):
        task = actions.add_parser(label)
        task.add_argument("--packet-sha256", required=True)
        if label == "root-replay":
            task.add_argument("--source-root", type=Path, required=True)
            task.add_argument("--receipt", type=Path, required=True)
    for label in ("authored-worker", "root-worker"):
        task = actions.add_parser(label)
        task.add_argument("sdk", type=Path)
    args = parser.parse_args()
    if args.action in ("root-replay", "root-worker") and os.name != "nt":
        parser.error("protected replay belongs to the root-controlled Windows guest")
    if args.action == "stage":
        result = stage(args.revision, args.destination)
    elif args.action in ("authored-worker", "root-worker"):
        try:
            result = worker(args.sdk, args.action == "authored-worker")
        except Exception:
            if args.action == "authored-worker":
                raise
            print('{"passed":false,"diagnostic":"standalone_history_worker_refused"}')
            return 3
    elif args.action == "verify":
        result = evaluate(HERE.parent, args.packet_sha256)
    else:
        require(not args.receipt.resolve().is_relative_to(HERE.parent), "receipt belongs outside the frozen packet")
        with args.receipt.open("xb") as output:
            try:
                result = evaluate(HERE.parent, args.packet_sha256, args.source_root)
            except Exception:
                result = {"schema": RECEIPT, "passed": False, "packet_sha256": args.packet_sha256,
                          "diagnostic": "standalone_history_replay_refused"}
            output.write(encode(result))
        print(json.dumps({"passed": result["passed"], "receipt_sha256": digest(encode(result))}))
        return 0 if result["passed"] else 3
    sys.stdout.buffer.write(encode(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
