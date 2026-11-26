"""Verify and unpack the private exact-byte vendor boss research inputs."""

from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import sys
from zipfile import BadZipFile, ZipFile


MANIFEST_SCHEMA = "kit.sw2026.vendor-boss-private-replay.v1"
MEMBER_NAME = re.compile(r"(?:[A-Za-z0-9]+/)+[A-Za-z0-9]+\.(?:json|SLDPRT)")
LIMIT = 16 * 1024 * 1024


def checked_payload(path, identity):
    with path.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT or len(raw) != identity["bytes"] or sha256(raw).hexdigest() != identity["sha256"]:
        raise ValueError("private replay archive differs from its manifest")
    return raw


def verified_members(raw, expected):
    with ZipFile(BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = {info.filename for info in entries}
        if (
            len(entries) != len(expected)
            or names != set(expected)
            or len({name.casefold() for name in names}) != len(names)
        ):
            raise ValueError("private replay archive has a different member inventory")
        if sum(info.file_size for info in entries) > LIMIT:
            raise ValueError("private replay archive exceeds the expanded size limit")
        members = {}
        for info in entries:
            name = info.filename
            if MEMBER_NAME.fullmatch(name) is None or info.file_size != expected[name]["bytes"]:
                raise ValueError("private replay archive has an invalid member path or extent")
            content = archive.read(info)
            if sha256(content).hexdigest() != expected[name]["sha256"]:
                raise ValueError(f"private replay member {name} has a different digest")
            members[PurePosixPath(name)] = content
        return members


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.manifest.open("rb") as stream:
        index = json.load(stream)
    if index["schema"] != MANIFEST_SCHEMA or not index["members"]:
        raise ValueError("private replay bundle manifest is unsupported")
    raw = checked_payload(args.bundle, index["bundle"])
    members = verified_members(raw, index["members"])
    args.output.mkdir(parents=False, exist_ok=False)
    for path, content in members.items():
        output = args.output.joinpath(*path.parts)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            stream.write(content)
    print(json.dumps({"bundle_sha256": index["bundle"]["sha256"], "members": len(members)}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, BadZipFile) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(3) from error
