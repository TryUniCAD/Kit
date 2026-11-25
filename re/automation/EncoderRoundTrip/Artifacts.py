import hashlib
import json
import os
from pathlib import Path
import stat


NATIVE_LIMIT = 256 * 1024 * 1024
DOCUMENT_LIMIT = 64 * 1024 * 1024
RECORD_LIMIT = 16 * 1024 * 1024


def canonical_json(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def absolute(path):
    return Path(os.path.abspath(Path(path).expanduser()))


def exists(path):
    return os.path.lexists(path)


def require_directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"expected a directory without links or reparse points: {path}")


def write_artifact(directory, name, payload):
    with (directory / name).open("xb") as target:
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())
    return {"path": name, "sha256": digest(payload), "bytes": len(payload)}


def read_record(payload):
    def unique_pairs(pairs):
        value = dict(pairs)
        if len(pairs) != len(value):
            raise ValueError("JSON record contains duplicate keys")
        return value

    def reject_constant(value):
        raise ValueError(f"JSON record contains a nonfinite number: {value}")

    value = json.loads(payload, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("JSON record must be an object")
    return value
