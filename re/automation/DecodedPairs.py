import hashlib
import os
import stat
from pathlib import Path

from SemanticComparison import bounded_json, pinned_bytes

MAX_PAIRS = 1000


def fail_walk(error):
    raise error


def file_pin(path, limit):
    details = path.lstat()
    if (
        not stat.S_ISREG(details.st_mode)
        or details.st_size > limit
        or getattr(details, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise ValueError("input must be a bounded plain regular file")
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    with os.fdopen(descriptor, "rb") as source:
        opened = os.fstat(source.fileno())
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size > limit
            or (opened.st_dev, opened.st_ino) != (details.st_dev, details.st_ino)
        ):
            raise ValueError("input changed before its bounded plain file read")
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError("input exceeds its byte limit")
    digest = hashlib.sha256(data).hexdigest()
    pinned_bytes(path, digest, limit)
    return digest


def directory_files(root, pattern):
    details = root.lstat()
    if not root.is_dir() or root.is_symlink() or (
        getattr(details, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise ValueError("input directory must be an existing plain directory")
    result = {}
    visited = 0
    for directory, folders, files in os.walk(root, followlinks=False, onerror=fail_walk):
        visited += 1 + len(folders) + len(files)
        if visited > 100000:
            raise ValueError("input directory exceeds its discovery budget")
        base = Path(directory)
        for name in folders:
            child = base / name
            details = child.lstat()
            if child.is_symlink() or (
                getattr(details, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            ):
                raise ValueError("input directory contains a linked directory")
        for name in files:
            child = base / name
            relative = child.relative_to(root)
            if relative.match(pattern):
                if child.is_symlink():
                    raise ValueError("input directory contains a linked JSON file")
                result[relative.as_posix()] = child
                if len(result) > MAX_PAIRS:
                    raise ValueError("input directory exceeds 1000 selected files")
    return result


def directory_pairs(left, right, pattern):
    first = directory_files(left, pattern)
    second = directory_files(right, pattern)
    keys = sorted(first.keys() | second.keys())
    if not keys or len(keys) > MAX_PAIRS:
        raise ValueError("select between 1 and 1000 document pairs")
    if any(len(key) > 4096 for key in keys):
        raise ValueError("relative document identities exceed 4096 characters")
    return [
        {"id": key, "left": first.get(key), "right": second.get(key)}
        for key in keys
    ]


def manifest_pairs(path):
    digest = file_pin(path, 1024 * 1024)
    value = bounded_json(pinned_bytes(path, digest, 1024 * 1024))
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "pairs"}
        or type(value["version"]) is not int
        or value["version"] != 1
        or not isinstance(value["pairs"], list)
        or not 1 <= len(value["pairs"]) <= MAX_PAIRS
    ):
        raise ValueError("manifest requires version 1 and 1 through 1000 pairs")
    result = []
    identities = set()
    for entry in value["pairs"]:
        if not isinstance(entry, dict) or set(entry) != {"id", "left", "right"}:
            raise ValueError("each manifest pair requires id left and right")
        if any(
            not isinstance(entry[key], str) or not 1 <= len(entry[key]) <= 4096
            for key in ("id", "left", "right")
        ):
            raise ValueError("manifest identities and paths require bounded text")
        if entry["id"] in identities:
            raise ValueError("manifest pair identities must be unique")
        identities.add(entry["id"])
        result.append(
            {
                "id": entry["id"],
                **{
                    side: path.parent / entry[side]
                    for side in ("left", "right")
                },
            }
        )
    return result, digest
