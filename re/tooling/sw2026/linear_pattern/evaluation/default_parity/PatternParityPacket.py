from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath, PureWindowsPath
from stat import S_IFMT, S_IFREG
from subprocess import run
from zipfile import ZipFile
import json
import re


TRIAL = "LinearPatternDefaultParity01"
PRIOR_TRIAL = "LinearPatternDatumEvaluation01"
SOURCE_TRIAL = "LinearPatternDatumHoldout01"
PRIVATE_ROOT = r"C:\KitLinearPatternDefaultParity01"
BUILD = "34.5.2.0604"
SDK_REVISION = "e393f3080141976513fe0f397d7766b97879a63c"
SDK_TREE = "46bc99536814f1a0eb5b28f6a49099d71b2a15ba"
PRIOR_FREEZE = "98bea34ca278386abc71a79644d5404304a35d355950ad025716ee8a513b1477"
PRIOR_RESULT = "abaa363a2722c95166fe33cc668baf4555582b172e663ca67b42b775c9bacfb2"
DEFAULT_SMOKE = "ef52c12bc4a22a0de666b043ad586871a0bdfa03e877ac62e591b40dfbaa2df7"
WORKER = "re/tooling/sw2026/linear_pattern/evaluation/default_parity/PatternDefaultWorker.py"
GUARD = "tests/Convert/Solidworks/Research/ConstructionGuard.py"
PACKET_FILES = {"Source.zip", "Tools/PatternParityPacket.py", "Tools/RunPatternDefaultParity.py"}
SCHEMA = "kit.sw2026.oblique-pattern-default-parity-packet.v1"
SLOTS = ("Slot01", "Slot02")
STATES = ("original", "spacing", "instances")
APPLICATIONS = {"Swapp", "pythoncom", "pywintypes", "win32com", "FreeCAD", "FreeCADGui", "adsk"}


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False, ensure_ascii=False, indent=2) + "\n").encode()


def identity(raw):
    return {"sha256": digest(raw), "bytes": len(raw)}


def checked(path, pin):
    require(path.is_file() and not path.is_symlink() and not path.is_junction(), "missing or linked packet file")
    raw = path.read_bytes()
    if type(pin) is str:
        require(digest(raw) == pin, "packet file digest changed")
    else:
        require(identity(raw) == pin, "packet file identity changed")
    return raw


def exclusive(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)


def safe_python(name):
    relative = PurePosixPath(name)
    require(relative.as_posix() == name and relative.suffix == ".py" and not relative.is_absolute()
            and ".." not in relative.parts and all(not part.endswith((" ", ".")) for part in relative.parts)
            and not any(char in name for char in ("\\", ":", "*", "?", '"', "<", ">", "|", "\0"))
            and not any(PureWindowsPath(part).is_reserved() for part in relative.parts)
            and (name.startswith(("src/", "re/tooling/sw2026/"))
                 or name == GUARD or name.startswith("tests/") and name.endswith("/__init__.py")),
            "member is outside the bounded Python code inventory")
    return relative


def pinned_result(raw):
    value = json.loads(raw)
    require(value["schema"] == "kit.sw2026.oblique-linear-pattern-heldout-result.v1"
            and value["freeze_sha256"] == PRIOR_FREEZE and value["build"] == BUILD
            and value["private_data_guest_only"] is True and value["passed"] is True
            and value["qualified_cases"] == 2 and value["complete_distinct_processes"] == 18
            and len(value["controls"]) == 4 and all(row["passed"] is True for row in value["controls"])
            and len(value["phases"]) == 14 and all(row["passed"] is True for row in value["phases"])
            and tuple(row["slot"] for row in value["cases"]) == SLOTS
            and all(row["passed"] is True and row["runtime_input_reads"] == 0
                    and row["compared_snapshots"] == 6 and set(row["saved_derivatives"]) == set(STATES[1:])
                    and all(item["reopened"] is True for item in row["saved_derivatives"].values())
                    for row in value["cases"]),
            "prior native qualification did not close both source slots")
    return value


def verified_packet(packet, pin):
    require(re.fullmatch("[0-9a-f]{64}", pin) and packet.name == "Packet" and packet.parent.name == TRIAL,
            "unexpected parity packet locator or digest")
    value = json.loads(checked(packet / "Manifest.json", pin))
    require(value["schema"] == SCHEMA and value["sdk_revision"] == SDK_REVISION and value["sdk_src_tree"] == SDK_TREE
            and value["native_build"] == BUILD and value["prior_freeze_sha256"] == PRIOR_FREEZE
            and value["prior_result_sha256"] == PRIOR_RESULT and value["disclosed_default_sha256"] == DEFAULT_SMOKE
            and value["slots"] == list(SLOTS) and value["writer_worker"] == WORKER,
            "unexpected parity proof or production revision")
    members = value["source_members"]
    require(type(members) is dict and {WORKER, GUARD} <= members.keys()
            and len({name.casefold() for name in members}) == len(members), "invalid source closure")
    for name in members:
        safe_python(name)
    require(set(value["packet_files"]) == PACKET_FILES
            and {path.relative_to(packet).as_posix() for path in packet.rglob("*") if path.is_file()}
            == PACKET_FILES | {"Manifest.json"}, "parity packet contents changed")
    for name, pin_value in value["packet_files"].items():
        target = packet.joinpath(*PurePosixPath(name).parts)
        require(target.resolve(strict=True).is_relative_to(packet), "packet member escaped its root")
        checked(target, pin_value)
    return value


def unpack_sources(payload, members, destination):
    with ZipFile(BytesIO(payload)) as archive:
        found = archive.infolist()
        require(len(found) == len(members) and {row.filename for row in found} == set(members),
                "Python archive member inventory changed")
        destination.mkdir(exist_ok=False)
        for row in found:
            relative = safe_python(row.filename)
            pin = members[row.filename]
            require(S_IFMT(row.external_attr >> 16) == S_IFREG and not row.is_dir()
                    and row.file_size == pin["bytes"], "invalid Python archive member")
            raw = archive.read(row)
            require(identity(raw) == pin, "Python archive member hash changed")
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            require(target.parent.resolve(strict=True).is_relative_to(destination.resolve()),
                    "archive destination escaped its private root")
            exclusive(target, raw)
    return destination.joinpath(*PurePosixPath(WORKER).parts)


def check_request(value):
    require(type(value) is dict and set(value) == {"document", "target"} and type(value["document"]) is dict
            and type(value["target"]) is dict and set(value["target"]) == {"PathName", "SavedAt"},
            "writer request must contain only neutral document wire and explicit target")
    return value


def check_product(value):
    require(type(value) is dict and set(value) == {
        "payload", "sha256", "bytes", "streams", "root_count", "typed_replays", "runtime_reads",
    }, "generated response has extra or missing proof fields")
    payload = b64decode(value["payload"], validate=True)
    require(len(payload) == value["bytes"] > 0 and digest(payload) == value["sha256"]
            and value["root_count"] == 24 and value["typed_replays"] == 9 and value["runtime_reads"] == 0
            and type(value["streams"]) is dict and len(value["streams"]) == 10
            and all(re.fullmatch("[0-9a-f]{64}", pin) for pin in value["streams"].values()),
            "generated response lost an archive or runtime guard")
    return value, payload


def invoke(python, entry, mode, raw, cwd):
    return run((str(python), "-I", "-B", str(entry), mode), cwd=cwd, input=raw,
               capture_output=True, check=False, timeout=90)
