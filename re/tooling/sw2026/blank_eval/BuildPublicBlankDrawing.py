import argparse
from codecs import lookup
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import sys
from uuid import UUID

from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.api import write_document

from PublicBlankIntent import neutral_drawing, pinned


class WriteGuard:
    def __init__(self, target):
        self.target = target
        self.prefix = f".{target.name}.kit-"
        self.active = False
        self.opened = []
        self.published = []
        self.denied = []

    def staging(self, path):
        return path.parent == self.target.parent and path.name.startswith(self.prefix)

    def event(self, name, args):
        if not self.active:
            return
        if name == "open":
            filename, mode, flags = args
            if isinstance(filename, (str, bytes)):
                path = Path(os.fsdecode(filename))
                if mode is None and self.staging(path) and path.is_dir():
                    return
                if (path.name == self.target.name and self.staging(path.parent)
                    and flags & (os.O_WRONLY | os.O_RDWR) == os.O_WRONLY
                    and mode in ("w", "x")):
                    self.opened.append(path)
                    return
            self.deny(name)
        if name in ("os.link", "os.rename"):
            source, target = map(Path, args[:2])
            if self.opened != [source] or target != self.target:
                self.deny(name)
            self.published.append(name)
        if name.startswith(("subprocess.", "socket.", "winreg.", "ctypes.")) or name in (
            "os.exec", "os.posix_spawn", "os.spawn", "os.system",
        ):
            self.deny(name)

    def deny(self, name):
        self.denied.append(name)
        raise RuntimeError(f"unexpected guarded operation: {name}")

    def __enter__(self):
        self.active = True
        return self

    def __exit__(self, *_):
        self.active = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--intent-sha256", required=True)
    parser.add_argument("--options", type=Path, required=True)
    parser.add_argument("--options-sha256", required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--route", choices=("extension", "solidworks.slddrw"), required=True)
    parser.add_argument("--epoch", type=int, required=True)
    parser.add_argument("--block-id", type=UUID, required=True)
    parser.add_argument("--writer-manifest-sha256", required=True)
    args = parser.parse_args()

    target = args.target
    if target != target.resolve() or not target.parent.is_dir() or target.exists():
        raise ValueError("use an unused absolute output in an existing directory")
    if args.report.exists() or args.report == target or args.block_id.version != 4:
        raise ValueError("use a new report and a version-four block identity")
    options = pinned(args.options, args.options_sha256)
    if options != {
        "schema": "kit.sw2026.public-blank-options.v1",
        "allow_carrier": False,
        "overwrite": False,
        "validate": True,
        "values": {"require_native_transfers": True, "require_self_contained": True},
    }:
        raise ValueError("explicit native write options differ")
    del options["schema"]
    doc = neutral_drawing(args.intent, args.intent_sha256, target.stem)
    for encoding in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(encoding)
    doc.AssertValid()
    GetDocumentCaps(doc)

    emitter = importlib.import_module("convert.adapters.solidworks.Core.DrawingWriting.EmitBlankDrawingMut")
    emitter.ReadTime = lambda: args.epoch
    emitter.AllocateBlockId = lambda: args.block_id
    dest_format = None if args.route == "extension" else args.route
    guard = WriteGuard(target)
    sys.addaudithook(guard.event)
    with guard:
        result = write_document(doc, target, destination_format=dest_format, **options)
    if (
        result.adapter != "solidworks.slddrw" or result.path != target
        or not result.application_usable or not result.vendor_loadable or result.dropped
        or result.requirements or result.carrier_capabilities
        or len(guard.opened) != 1 or len(guard.published) != 1 or guard.denied
    ):
        raise ValueError("public native result or staging evidence differs")
    payload = target.read_bytes()
    if result.bytes_written != len(payload) or any(target.parent.glob(guard.prefix + "*")):
        raise ValueError("staged output size or cleanup differs")

    old_identity = target.stat()
    try:
        with guard:
            write_document(doc, target, destination_format=dest_format, **options)
    except FileExistsError:
        pass
    else:
        raise ValueError("public writer unexpectedly replaced an existing file")
    new_identity = target.stat()
    if (
        new_identity != old_identity or target.read_bytes() != payload
        or len(guard.opened) != 1 or len(guard.published) != 1 or guard.denied
    ):
        raise ValueError("the no-overwrite refusal changed output or attempted staging")
    report = {
        "schema": "kit.sw2026.public-blank-guarded-build.v1",
        "route": args.route,
        "writer_epoch": args.epoch,
        "block_id": str(args.block_id),
        "target_path": str(target),
        "intent_sha256": args.intent_sha256,
        "explicit_options_sha256": args.options_sha256,
        "writer_manifest_sha256": args.writer_manifest_sha256,
        "runtime_guard_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "data_file_reads": 0,
        "native_template_reads": 0,
        "cad_runtime_calls": 0,
        "dropped": [],
        "atomic_write_verified": True,
        "no_overwrite_verified": True,
        "publish_operation": guard.published[0],
        "bytes": len(payload),
        "output": {"path": str(target), "sha256": sha256(payload).hexdigest()},
    }
    with args.report.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "sha256": report["output"]["sha256"], "bytes": len(payload)}))


if __name__ == "__main__":
    main()
