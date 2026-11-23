from argparse import ArgumentParser
from base64 import b64decode, b64encode
from datetime import datetime
import json
from pathlib import Path
from struct import pack_into
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveAssemblyContentIndex import (
    MEASUREMENTS,
    PROOF,
    PROOF_PIN,
    REPO,
    checked,
    fingerprint,
    proof_guard,
    require,
    source_cases,
    wire,
)
from ObserveUnqliteStore import Observer

from convert.adapters.solidworks.Archive.Exchange.DatabaseClock import (
    DecodeUnqliteClock,
    EncodeUnqliteClock,
)
from convert.adapters.solidworks.Archive.Exchange.ReadUnqliteFree import ReadUnqliteFree
from convert.adapters.solidworks.Archive.Exchange.ReadUnqliteStore import (
    ReadUnqliteStore,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteLayout import (
    KUnqliteBucket,
    KUnqliteFree,
    KUnqlitePageSize,
)
from convert.adapters.solidworks.Archive.Exchange.WriteUnqliteStore import (
    WriteUnqliteStore,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive

BASE = "2e3c2ab7c83ae5f6632dbc0bf64482f7546d8bab"
UPSTREAM = "ddb1687036d207bbfc67b98cb470fe52ddf22f62"
CONFIG = "Contents/3DExperienceExchange_ConfigHeader"
MODEL = "Contents/3DExperienceExchange2"
RENAMED = "ConcentricNameBaseSetterRetry01/NativePacket02/Native/Source/CustomNameOwnershipControl.SLDASM"
RENAMED_PIN = "481a13c6f3c068d6df56521b7b0bb31c63f13404dbc0e2f469b0ca6d4034c83c"


def refusals(payload):
    start = 2 * KUnqlitePageSize
    active, free, _ = KUnqliteBucket.unpack_from(payload, start)
    changes = (
        ("wrong_pager", 7, ">I", 0xAF213414),
        ("wrong_map", KUnqlitePageSize + 52, ">Q", 1),
        ("active_cycle", start + active + 16, ">H", active),
        ("bad_cell_hash", start + active, ">I", 0),
        ("free_cycle", start + free, ">H", free),
        ("unallocated_tail", start + free + 2, ">H", len(payload) - start - free - 1),
    )
    results = {}
    for label, position, frame, value in changes:
        data = bytearray(payload)
        pack_into(frame, data, position, value)
        try:
            ReadUnqliteStore(bytes(data))
        except ValueError as error:
            results[label] = str(error)
        else:
            raise ValueError("physical store accepted malformed input " + label)
    return results


def worker(request):
    clock = datetime.fromisoformat(request["created"])
    records = tuple(
        (key.encode("utf-8"), wire(properties))
        for key, properties in request["records"]
    )
    attempts = proof_guard()
    stamp = EncodeUnqliteClock(clock)
    data = WriteUnqliteStore(stamp, records)
    store = ReadUnqliteStore(data)
    require(
        store.ClockValue == stamp and store.Records == records and not attempts,
        "guarded physical codec changed model records or read external input",
    )
    return {
        "payload": b64encode(data).decode("ascii"),
        "sha256": fingerprint(data),
        "clock": DecodeUnqliteClock(store.ClockValue).isoformat(),
        "records": len(records),
        "runtime_external_accesses": len(attempts),
        "refusals": refusals(data),
    }


def checked_observation(observer, folder, data, records):
    path = folder / "Generated.unqlite"
    if path.exists():
        raise ValueError("reference observation requires a fresh local path")
    with path.open("xb") as stream:
        stream.write(data)
    return observer.inspect(path, records)


def source_receipts(args, observer):
    ownership = json.loads(checked(MEASUREMENTS / PROOF, PROOF_PIN))
    sources = (
        *source_cases(args.disclosures, ownership),
        ("Renamed", args.disclosures / RENAMED, RENAMED_PIN),
    )
    data = {}
    for label, filepath, pin in sources:
        archive = SldprtArchive.from_bytes(checked(filepath, pin))
        streams = {}
        for name in (CONFIG, MODEL):
            saved = archive.require(name)
            store = ReadUnqliteStore(saved)
            canonical = WriteUnqliteStore(store.ClockValue, store.Records)
            require(
                ReadUnqliteStore(canonical) == store
                and (name == CONFIG) == (canonical == saved),
                "scoped physical exchange layout changed",
            )
            require(
                EncodeUnqliteClock(DecodeUnqliteClock(store.ClockValue))
                == store.ClockValue,
                "source database clock differs from the typed layout",
            )
            bucket = saved[2 * KUnqlitePageSize :]
            _, first_free, _ = KUnqliteBucket.unpack_from(bucket)
            free_blocks = ReadUnqliteFree(bucket, first_free)
            discarded = sum(
                sum(bool(byte) for byte in bucket[start + KUnqliteFree.size : end])
                for start, end in free_blocks
            )
            require(
                (name == MODEL) == (discarded > 0), "free-space residue scope changed"
            )
            with TemporaryDirectory(prefix="KitExchangeObserve.") as temporary:
                independent = checked_observation(
                    observer, Path(temporary), canonical, store.Records
                )
            streams[name] = {
                "saved_sha256": fingerprint(saved),
                "canonical_sha256": fingerprint(canonical),
                "exact_physical_reconstruction": canonical == saved,
                "saved_free_blocks": len(free_blocks),
                "saved_inactive_nonzero_bytes": discarded,
                "live_records": independent,
                "clock": DecodeUnqliteClock(store.ClockValue).isoformat(),
            }
        data[label] = {"source_sha256": pin, "streams": streams}
    require(len(data) == 12, "physical exchange evidence scope changed")
    return data


def authored_controls(observer):
    requests = (
        {
            "created": "2026-01-02T03:04:07",
            "records": [("main", {"assembly": "assembly 17", "units": "mm"})],
        },
        {
            "created": "2026-12-12T07:29:38",
            "records": [
                ("layout", {"width": 17}),
                ("dimensions", {"offset": 3, "span": 42}),
                ("配置", {"count": 3}),
                ("owner", {"placements": [17, 23]}),
            ],
        },
    )
    result = []
    for request in requests:
        command = (sys.executable, "-I", "-B", str(HERE), "--worker")
        first, second = (
            subprocess.run(
                command, input=wire(request), capture_output=True, timeout=90
            )
            for _ in range(2)
        )
        require(
            first.returncode == second.returncode == 0
            and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "guarded fresh stores differ",
        )
        observed = json.loads(first.stdout)
        payload = b64decode(observed.pop("payload"), validate=True)
        expected = tuple(
            (key.encode("utf-8"), wire(value)) for key, value in request["records"]
        )
        with TemporaryDirectory(prefix="KitExchangeAuthored.") as folder:
            count = checked_observation(observer, Path(folder), payload, expected)
        require(
            count == observed["records"] and fingerprint(payload) == observed["sha256"],
            "independent record count or generated bytes changed",
        )
        result.append(observed)
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosures", type=Path)
    parser.add_argument("--reference-library", type=Path)
    parser.add_argument("--reference-source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin))))
        return
    require(
        args.disclosures is not None
        and args.reference_library is not None
        and args.reference_source is not None
        and args.output is not None,
        "bind disclosures, independent reader and output",
    )
    observer = Observer(args.reference_library)
    sources = source_receipts(args, observer)
    authored = authored_controls(observer)
    record = {
        "schema": "kit.sw2026.unqlite-exchange-store.v1",
        "base": BASE,
        "reference_commit": UPSTREAM,
        "reference_version": observer.version,
        "reference_source_sha256": fingerprint(args.reference_source.read_bytes()),
        "reference_library_sha256": fingerprint(args.reference_library.read_bytes()),
        "guarded_generated_workers": 4,
        "boxed_sources": sources,
        "authored_contrasts": authored,
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
        "codec_sha256": {
            file.name: fingerprint(file.read_bytes())
            for file in sorted(
                (REPO / "src/convert/adapters/solidworks/Archive/Exchange").glob("*.py")
            )
        },
    }
    data = wire(record)
    with args.output.open("xb") as out:
        out.write(data)
    print(
        json.dumps(
            {
                "sha256": fingerprint(data),
                "source_databases": 2 * len(sources),
                "authored_controls": len(authored),
            }
        )
    )


if __name__ == "__main__":
    main()
