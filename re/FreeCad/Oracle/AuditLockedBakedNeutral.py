from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path, PurePosixPath
import json
import os
import sys


FILES = ("Baked01.FCStd", "Baked02.FCStd", "ParametricControl.FCStd")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, digest, owner):
    require(path.resolve(strict=True) == path and path.is_relative_to(owner) and path.is_file(),
            "checked input must be one canonical owned file")
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == digest, "checked input SHA-256 differs")
    return raw


def verified_sdk(snapshot, pin):
    manifest = json.loads(checked(snapshot / "CodeManifest.json", pin, snapshot))
    code = snapshot / "CodeRoot"
    pinned = {}
    for name, digest in manifest["files_sha256"].items():
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and ".." not in relative.parts and relative.suffix == ".py",
                "invalid frozen Python source path")
        if relative.parts[0] == "src":
            pinned[name] = digest
    sdk = code / "src"
    require(pinned and set(pinned) == {path.relative_to(code).as_posix() for path in sdk.rglob("*.py")},
            "frozen SDK inventory is incomplete")
    for name, digest in pinned.items():
        checked(code / name, digest, code)
    return sdk, manifest


def seal_neutral(args):
    require(os.name == "nt", "locked native source decoding requires the Windows guest")
    snapshot = args.snapshot.resolve(strict=True)
    sdk, manifest = verified_sdk(snapshot, args.snapshot_sha256)
    author = args.packet.resolve(strict=True)
    require(len(author.drive) == 2 and author.drive.endswith(":") and author.name == "Packet01",
            "native source custody must be on the fixed guest drive")
    lock = json.loads(checked(author / "PrewriterSourceLock01.json", args.lock_sha256, author))
    require(lock["passed"] and lock["baked_sources"] == 2 and lock["live_parametric_controls"] == 1
            and lock["writer_outputs"] == lock["fcstd_conversion_credit"] == 0,
            "locked source roles or prewriter authority differ")
    sys.path.insert(0, str(sdk))
    from convert import open_document

    neutral = author / "StrictNeutral01"
    neutral.mkdir(exist_ok=False)
    rows = []
    for index, (name, identity) in enumerate(zip(FILES, lock["inputs"], strict=True), start=1):
        source = author / name
        checked(source, identity["file_sha256"], author)
        document = open_document(source)
        document.assert_valid()
        require(document.source.sha256 == identity["file_sha256"] and document.brep is not None
                and len(document.brep.bodies) == len(document.bodies) == 1,
                "the strict reader did not bind the complete owned solid")
        model = (document.to_json() + "\n").encode()
        with (neutral / f"Source{index:02d}.json").open("xb") as target:
            target.write(model)
        checked(source, identity["file_sha256"], author)
        rows.append({"slot": index, "source_file_sha256": identity["file_sha256"],
                     "source_shape_sha256": identity["shape_sha256"], "neutral_sha256": sha256(model).hexdigest(),
                     "baked_source": identity["standalone_baked"], "body_count": 1,
                     "complete_strict_read": True})
    require(not any(name in ("FreeCAD", "Part", "pythoncom", "pywintypes") or name.startswith("win32com")
                    for name in sys.modules), "strict neutral parsing loaded a vendor runtime")
    receipt = {"schema": "kit.freecad.locked-baked-strict-neutral.v1", "source_lock_sha256": args.lock_sha256,
               "snapshot_sha256": args.snapshot_sha256, "sdk_revision": manifest["writer_revision"],
               "sdk_tree": manifest["sdk_tree"], "process_python": list(sys.version_info[:3]), "slots": rows,
               "host_protected_source_reads": 0, "native_processes_started": 0, "writer_outputs": 0, "passed": True}
    raw = (json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with (neutral / "NeutralLock.json").open("xb") as out:
        out.write(raw)
    return {**receipt, "neutral_lock_sha256": sha256(raw).hexdigest()}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--lock-sha256", required=True)
    arguments = parser.parse_args()
    try:
        result = seal_neutral(arguments)
    except Exception as error:
        print(json.dumps({"passed": False, "error_type": type(error).__name__, "writer_outputs": 0}))
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True))
