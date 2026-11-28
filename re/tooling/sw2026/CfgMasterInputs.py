from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "re/solidworks/measurements/2026/ConfigFieldModesSource01.json"
FIXTURE = "re/solidworks/v2026/corpus/part-properties/CircularProperties.SLDPRT"
SCAN = "a7c48f805262e5147f3aebb9cf792b87b24b5b0e"
PART_HASHES = {
    "circle": "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23",
    "ladder": "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
    "concave": "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
}


def digest(data):
    return sha256(data).hexdigest()


def fingerprint(model):
    return digest(json.dumps(model, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def disclosed(name, archive_type, read_version):
    row = json.loads(SOURCE.read_bytes())["controls"][name]
    data = (ROOT / (FIXTURE if name == "circle" else row["path"])).read_bytes()
    require(digest(data) == row["source_sha256"] == PART_HASHES[name], "disclosed original digest differs")
    archive = archive_type.from_bytes(data)
    config = archive.require("Contents/Config-0")
    header = archive.require("Contents/Config-0-ModelHeader")
    require(archive.format_version == 4 and read_version(archive.streams) == 19000,
            "disclosed archive version differs")
    require(digest(config) == row["config_sha256"] and digest(header) == row["header_sha256"],
            "disclosed stream digest differs")
    return row, archive, header, config


def guard_runtime():
    from codecs import lookup
    from TraceCfgFont import audit_run

    accesses = []

    def observe(event, arguments):
        try:
            audit_run(event, arguments)
        except PermissionError:
            accesses.append(event)
            raise

    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(observe)
    return accesses
