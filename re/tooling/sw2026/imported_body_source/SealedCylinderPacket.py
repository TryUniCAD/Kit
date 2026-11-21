from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re

SCHEMA = "kit.sw2026.sealed-periodic-import-evaluation-job.v1"
LOCK_SCHEMA = "kit.sw2026.sealed-periodic-import-build-lock.v1"
RESULT_SCHEMA = "kit.sw2026.sealed-periodic-import-evaluation.v1"
LOCK_REVISION = "1e4ef213bbf7551eedd10f9ca76ecde89b3bc4cc"
LOCK_PATH = "re/solidworks/measurements/2026/SealedPeriodicImportedSourceLock01.json"
LOCK_SHA256 = "8f63cec25adb2adc5257b2e7be361a11d9ef1c39f4149ec9bb7ff67010ea24ab"
LOCK_TRANSPORT_SHA256 = (
    "ee905a2264c80dc4d3c78643caf465c8696fe448e0324c104737a767bc2a9f63"
)
CONSTRUCTION_PATH = "re/solidworks/measurements/2026/SdkBareCylinderComposition01.json"
CONSTRUCTION_SHA256 = "ccbe76220f8be81739305f8fc8a3de9fbd45d86f549b42880d6df52c9b0094e0"
WRITER_REVISION = "492f4f40bfdbecb5c3cdc7a964c96f851be523d7"
COMPARATOR_REVISION = "090620126fcc73d064b83aff722574f2ce29491d"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
VERSION = "34.5.2.0604"
SOURCE_ROOT = PureWindowsPath(r"C:\KitImportedBodySources83")
SLOTS = ("CylinderSlot01", "CylinderSlot02")
FEATURE = "Imported geometry"
GAUGE = "least-aligned positive cartesian vector projected into the signed-axis normal plane"
OMITTED = [
    "original document and body labels",
    "original native feature identity and system tree",
    "original seam parameterization",
    "original provenance and native payload",
    "original annotations and presentation scene",
    "original document properties and material",
    "original native configuration metadata",
    "original units display settings and save bookkeeping",
]
AUTHOR_TOOLS = (
    "AuthorCurves.py",
    "AuthorRectangleAnchors.py",
    "InspectFresh.py",
    "OracleIdentity.py",
    "Swapp.py",
)
IMPORT_TOOLS = (
    "AuthorImportedBody.py",
    "ObserveCylinderExchange.py",
    "ObserveKernelBodyRestore.py",
    "ObserveKernelExchange.py",
    "ObserveLocalCylinderPart.py",
    "ObserveLocalImportedPart.py",
    "RunImportedBodySources.py",
    "SealedCylinderSource.py",
)
PROTOCOL_TOOLS = (
    "EvaluateSealedCylinder.py",
    "ProduceSealedCylinder.py",
    "SealedCylinderModel.py",
    "SealedCylinderPacket.py",
)
GUARD_FILES = (
    "tests/__init__.py",
    "tests/Convert/__init__.py",
    "tests/Convert/Solidworks/__init__.py",
    "tests/Convert/Solidworks/Research/ConstructionGuard.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def is_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def is_revision(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value) is not None


def unique_object(rows):
    result = {}
    for name, value in rows:
        require(name not in result, "duplicate manifest key")
        result[name] = value
    return result


def parse(data):
    return json.loads(data, object_pairs_hook=unique_object)


def encode(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def checked(path, checksum, *, allow_empty=False):
    require(
        is_digest(checksum) and path.is_file() and not path.is_symlink(),
        "missing or invalid checked file",
    )
    length = path.stat().st_size
    require(
        (allow_empty or length > 0) and length <= 64 * 1024**2,
        "checked file size is outside this packet profile",
    )
    data = path.read_bytes()
    require(
        len(data) == length and digest(data) == checksum,
        "checked file differs from its locked identity",
    )
    return data


def guest_directory(value):
    require(
        type(value) is str
        and re.fullmatch(r"C:\\KitPeriodicImportEval[0-9]{2}", value),
        "use a fresh C:\\KitPeriodicImportEvalNN directory",
    )
    return PureWindowsPath(value)


def source_lock(data):
    document = parse(data)
    require(
        digest(data) == LOCK_SHA256
        and document["schema"] == "kit.sw2026.imported-body-source.v1"
        and document["cohort"] == "sealed-topology"
        and document["source_profile"] == "single_closed_periodic_cylinder"
        and document["oracle_version"] == VERSION
        and document["oracle_sha256"] == ORACLE
        and document["passed"] is True
        and document["controls_healthy"] is True
        and document["distinct_processes"] == 6
        and document["periodic_source_observations"] == 8
        and document["heldout_sources_locked"] == 2
        and document["heldout_payloads_shared"] == document["writer_outputs"] == 0
        and document["native_writer_acceptance"] is False
        and tuple(document["sources"]) == SLOTS
        and is_digest(document["specifications_sha256"])
        and 0
        < document["specifications_locked_at_unix_s"]
        < document["source_batch_locked_at_unix_s"],
        "the opaque prospective source lock differs",
    )
    for slot in SLOTS:
        binding = document["sources"][slot]
        require(
            set(binding)
            == {"source_sha256", "author_record_sha256", "reopen_record_sha256"}
            and all(map(is_digest, binding.values())),
            "source lock contains unsupported observations",
        )
    return document


def frozen_names(root):
    names = set()
    for directory in (root / "Code", root / "Tools"):
        require(
            directory.is_dir() and not directory.is_symlink(),
            "frozen directory is absent or indirect",
        )
        for path in directory.rglob("*"):
            require(not path.is_symlink(), "frozen closure contains an indirect member")
            if path.is_file():
                names.add(path.relative_to(root).as_posix())
    return names


def verify_packet(path, checksum):
    require(
        path.is_absolute() and path.name == "Job.json" and not path.is_symlink(),
        "use the regular staged Job.json",
    )
    root = path.parent
    job = parse(checked(path, checksum))
    require(
        set(job)
        == {
            "schema",
            "writer_revision",
            "writer_committed_at",
            "protocol_revision",
            "source_lock_revision",
            "source_lock_sha256",
            "source_transport_sha256",
            "construction_sha256",
            "oracle_version",
            "oracle_sha256",
            "control_sha256",
            "guest_root",
            "source_root",
            "files_sha256",
        }
        and job["schema"] == SCHEMA
        and job["writer_revision"] == WRITER_REVISION
        and is_revision(job["protocol_revision"])
        and job["source_lock_revision"] == LOCK_REVISION
        and job["source_lock_sha256"] == LOCK_SHA256
        and job["source_transport_sha256"] == LOCK_TRANSPORT_SHA256
        and job["construction_sha256"] == CONSTRUCTION_SHA256
        and job["oracle_version"] == VERSION
        and job["oracle_sha256"] == ORACLE
        and job["control_sha256"] == CONTROL
        and job["source_root"] == str(SOURCE_ROOT),
        "frozen evaluation job profile differs",
    )
    guest_directory(job["guest_root"])
    lock = source_lock(checked(root / "SourceLock.json", LOCK_SHA256))
    require(
        type(job["writer_committed_at"]) is int
        and lock["source_batch_locked_at_unix_s"] < job["writer_committed_at"] < 2**31,
        "writer commit must postdate the locked sources",
    )
    checked(root / "Construction.json", CONSTRUCTION_SHA256)
    checked(root / "Control.SLDPRT", CONTROL)
    require(
        {item.name for item in root.iterdir()}
        <= {
            "Job.json",
            "SourceLock.json",
            "Construction.json",
            "Control.SLDPRT",
            "Code",
            "Tools",
            "Result.json",
        },
        "unexpected public packet entry",
    )
    names = frozen_names(root)
    expected_tools = {
        "Tools/" + name for name in (*AUTHOR_TOOLS, *IMPORT_TOOLS, *PROTOCOL_TOOLS)
    }
    require(
        names == set(job["files_sha256"])
        and {name for name in names if name.startswith("Tools/")} == expected_tools
        and {name for name in names if name.startswith("Code/tests/")}
        == {"Code/" + name for name in GUARD_FILES}
        and any(name.startswith("Code/src/") for name in names)
        and all(
            name in expected_tools or name.startswith(("Code/src/", "Code/tests/"))
            for name in names
        ),
        "frozen SDK or tool inventory differs",
    )
    for name, identity in job["files_sha256"].items():
        checked(root / name, identity, allow_empty=name.startswith("Code/"))
    return job, lock


def atomic_receipt(path, value):
    pending = path.with_suffix(".json.tmp")
    with pending.open("xb") as output:
        output.write(encode(value))
    pending.replace(path)
