from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from struct import pack
import subprocess
import sys


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    if path.is_symlink() or digest(raw) != expected:
        raise ValueError(f"concentric replay input changed: {path.name}")
    return raw


def encode(value):
    return (dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def stop_runtime_access():
    reads = []

    def audit(event, args):
        if event in ("open", "os.system", "subprocess.Popen", "socket.connect"):
            reads.append(event)
            raise RuntimeError(f"archive replay attempted {event} after delivering its input")

    sys.addaudithook(audit)
    return reads


def change(root, case):
    fields = root.FieldsValue
    support = fields["f3c8"][0]["o"].FieldsValue
    selected = fields["f410"][0]["o"].FieldsValue
    facet = support["f58"].FieldsValue["fb0"].FieldsValue
    face = selected["f58"].FieldsValue
    persistent = face["fe8"].FieldsValue
    changes = {
        "lock": (fields, "f4b8", 2),
        "position": (fields, "f4c4", 1),
        "alignment": (fields, "f3b4", 3),
        "radius": (selected, "f100", 0.0),
        "local-vector": (selected, "has_f108", 0),
        "same-wrapper": (fields["f410"][0], "o", fields["f3c8"][0]["o"]),
        "facet-points": (facet, "has_points", 1),
        "facet-text": (facet, "f58_empty", 1),
        "face-alias": (face, "alias", 1),
        "missing-cap": (persistent["f10"][1], "f08", None),
        "lost-null": (persistent["f10"][2], "f08", persistent["f10"][1]["f08"]),
    }
    owner, field, value = changes[case]
    owner[field] = value


def worker(repo, request):
    sys.path.insert(0, str(repo / "src"))
    import encodings.utf_16_le

    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    raw = checked(Path(request["path"]), request["sha256"])
    audit = stop_runtime_access()
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    name = link.ConfigName + "-MatesList"
    source = archive.require(name)
    mode = request["mode"]
    malformed = request.get("malformed")
    if mode == "read-refusal":
        source = {
            "counter": pack("<i", link.ResolvedValue.MapValue.CounterValue + 1) + source[4:],
            "trailing": source + b"\x00",
            "truncated": source[:-1],
        }[malformed]
    try:
        graph = ReadMatesMut(source, link.ResolvedValue)
        classes = [root.ClassValue.NameValue for root in graph.RootsValue]
        if classes != request["classes"]:
            raise AssertionError(f"concentric or planar source classes changed: {classes}")
        if mode == "write-refusal":
            root, = graph.RootsValue
            change(root, malformed)
            WriteMatesMut(graph.RootsValue, link.ResolvedValue)
    except (ValueError, TypeError, KeyError) as error:
        if (mode == "read-refusal" or mode == "write-refusal") and not audit:
            return {"passed": True, "mode": mode, "malformed": malformed,
                    "exception": type(error).__name__, "diagnostic": str(error),
                    "runtime_access_attempts": len(audit)}
        raise
    if mode != "roundtrip":
        raise AssertionError(f"unqualified {malformed} case unexpectedly passed")
    cfg, seed = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
    resolved, emitted = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                      19000, seed.MapValue, link.ResolvedValue.ContextValue)
    mates, saved = WriteMatesMut(graph.RootsValue, emitted)
    streams = {link.ConfigName: cfg, link.StreamName: resolved, name: mates}
    if any(archive.require(key) != data for key, data in streams.items()):
        raise AssertionError("shared SDK did not reproduce every linked stream")
    left, right = graph.MapValue, saved.MapValue
    if (left.CounterValue != right.CounterValue or left.CounterValue != request["terminal"]
            or len(left.EntriesValue) != len(right.EntriesValue)
            or not all(a.IndexValue == b.IndexValue and (
                a.EntryValue is b.EntryValue if isinstance(a.EntryValue, ArchiveNode)
                else a.EntryValue == b.EntryValue
            ) for a, b in zip(left.EntriesValue, right.EntriesValue, strict=True))):
        raise AssertionError("shared SDK mate map lost exact class or object identity")
    return {
        "passed": True, "mode": mode, "classes": classes, "archive_sha256": request["sha256"],
        "map_base": graph.MapBase, "map_terminal": left.CounterValue,
        "map_owned_entries": len(left.EntriesValue), "runtime_access_attempts": len(audit),
        "streams": {key: {"bytes": len(data), "sha256": digest(data)} for key, data in streams.items()},
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(encode(worker(args.repo, loads(sys.stdin.buffer.read()))).decode(), end="")
        return
    inputs = loads(checked(args.manifest, args.manifest_sha256))
    positive = inputs["disclosed"]
    if (inputs["heldout_inputs_read"] != 0 or len(positive) != 6
            or any(row["classes"] != ["moMateConcentric"] for row in positive)
            or not inputs["planar_controls"]):
        raise ValueError("use three disclosed concentric source and edited pairs and named planar controls")
    negatives = []
    for step in ("counter", "trailing", "truncated"):
        negatives.append({**positive[0], "mode": "read-refusal", "malformed": step})
    for step in ("lock", "position", "alignment", "radius", "local-vector",
                 "same-wrapper", "facet-points", "facet-text", "face-alias", "missing-cap", "lost-null"):
        negatives.append({**positive[0], "mode": "write-refusal", "malformed": step})
    reports = []
    for item in (*positive, *inputs["planar_controls"], *negatives):
        request = {"mode": "roundtrip", **item}
        process = subprocess.run(
            [sys.executable, "-I", "-B", str(Path(__file__).resolve()), str(args.repo), "--worker"],
            input=encode(request), capture_output=True, check=False, timeout=60,
        )
        if process.returncode or process.stderr:
            raise ValueError(process.stderr.decode(errors="replace") or f"archive worker refused {item['case']}")
        report = loads(process.stdout)
        if report["passed"] is not True or report["runtime_access_attempts"] != 0:
            raise ValueError("archive worker did not pass its full checks")
        reports.append({"case": item["case"], "stdout_sha256": digest(process.stdout), "result": report})
    result = {
        "schema": "kit.sw2026.concentric-sdk-archive-replay.v1", "passed": True,
        "manifest_sha256": args.manifest_sha256, "tool_sha256": digest(Path(__file__).read_bytes()),
        "workers": len(reports), "concentric": len(positive), "planar": len(inputs["planar_controls"]),
        "malformed_refusals": len(negatives), "heldout_inputs_read": 0, "native_processes_started": 0,
        "public_concentric_projection_qualified": False, "generative_writer_qualified": False,
        "reports": reports,
    }
    raw = encode(result)
    with args.output.open("xb") as fd:
        fd.write(raw)
    print(dumps({"passed": True, "workers": len(reports), "result_sha256": digest(raw)}))


if __name__ == "__main__":
    main()
