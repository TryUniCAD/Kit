import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from struct import pack, unpack, unpack_from
import sys


def require(value, reason):
    if not value:
        raise ValueError(reason)


def digest(value):
    return sha256(value).hexdigest()


def single(value):
    return unpack("<f", pack("<f", value))[0]


def key_bits(value, wire_type):
    require(type(value) is int, "identity keys must be integers")
    low, high = (
        (-(1 << 31), (1 << 31) - 1) if wire_type == "i32" else (0, (1 << 32) - 1)
    )
    require(
        low <= value <= high and value != 0,
        "identity key is outside the nonzero wire domain",
    )
    return value & 0xFFFFFFFF


def hash_key(value):
    result = 0xCBF29CE484222325
    for shift in (0, 8, 16, 24):
        result = (
            (result ^ ((value >> shift) & 0xFF)) * 0x100000001B3
        ) & 0xFFFFFFFFFFFFFFFF
    return result


def reference_hash(value):
    raw = value.to_bytes(4, "little", signed=False)
    result = 14695981039346656037
    for byte in raw:
        result ^= byte
        result *= 1099511628211
        result %= 18446744073709551616
    return result


def native_order(keys, wire_type):
    require(wire_type in ("i32", "u32"), "identity wire type must be i32 or u32")
    require(
        type(keys) is list and 0 < len(keys) <= 12,
        "numeric profile needs one to twelve supplied keys",
    )
    bits = [key_bits(value, wire_type) for value in keys]
    require(
        len(set(bits)) == len(bits),
        "fresh registration requires distinct allocated IDs",
    )
    hashes = {value: hash_key(value) for value in bits}
    require(
        all(hashes[value] == reference_hash(value) for value in bits),
        "independent FNV calculations differ",
    )
    bucket_count = 8
    head = object()
    following = {head: head}
    previous = {head: head}
    occupied = {}
    retained = []
    history = []
    for ordinal, value in enumerate(bits):
        old_count = bucket_count
        before_bucket = hashes[value] & (old_count - 1)
        before_members = occupied.get(before_bucket, [])
        load = single(single(ordinal + 1) / single(old_count))
        growth = None
        if single(1.0) < load:
            minimum = max(8, ordinal + 1)
            requested = (
                old_count * 8
                if old_count < 512 and old_count * 8 >= minimum
                else minimum
            )
            bucket_count = 1 << ((requested - 1) | 1).bit_length()
            rebuilt = {}
            for existing in retained:
                bucket = hashes[existing] & (bucket_count - 1)
                require(
                    bucket not in rebuilt,
                    "numeric scope excludes actual rehash collisions",
                )
                rebuilt[bucket] = [existing]
            occupied = rebuilt
            growth = {
                "prospective_count": ordinal + 1,
                "load_binary32": load,
                "minimum_required_buckets": minimum,
                "requested_buckets": requested,
                "old_buckets": old_count,
                "new_buckets": bucket_count,
                "rehash_empty_bucket_count": len(retained),
                "rehash_splices": 0,
            }
        bucket = hashes[value] & (bucket_count - 1)
        require(
            bucket not in occupied,
            "numeric scope excludes an occupied final insertion bucket",
        )
        tail = previous[head]
        following[value] = head
        previous[value] = tail
        following[tail] = value
        previous[head] = value
        occupied[bucket] = [value]
        retained.append(value)
        history.append(
            {
                "ordinal": ordinal,
                "key": keys[ordinal],
                "key_bits": value,
                "hash64": hex(hashes[value]),
                "before_bucket_count": old_count,
                "before_bucket": before_bucket,
                "before_bucket_members": before_members,
                "growth": growth,
                "insertion_bucket_count": bucket_count,
                "insertion_bucket": bucket,
                "insertion_position": "shared sentinel",
            }
        )
    walked = []
    cursor = following[head]
    while cursor is not head:
        require(len(walked) < len(bits), "numeric forward list has a cycle")
        walked.append(cursor)
        require(following[previous[cursor]] == cursor, "numeric list aliases disagree")
        cursor = following[cursor]
    require(
        walked == bits, "numeric native list differs from its no-collision derivation"
    )
    signed = {
        value: value - (1 << 32) if value & (1 << 31) else value for value in bits
    }
    return {
        "wire_type": wire_type,
        "input_keys": keys,
        "serialized_key_order": [
            signed[value] if wire_type == "i32" else value for value in walked
        ],
        "serialized_key_bits": walked,
        "final_bucket_count": bucket_count,
        "final_mask": bucket_count - 1,
        "final_buckets_in_store_order": [
            hashes[value] & (bucket_count - 1) for value in walked
        ],
        "history": history,
        "wire_key_words_le_hex": b"".join(pack("<I", value) for value in walked).hex(),
        "claim": "collision-free completed insertion and rehash branches only; no native CAD acceptance",
    }


def read_image(args, record):
    relative = "re/tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py"
    path = args.root / relative
    require(
        digest(path.read_bytes()) == record["dependency_sha256"],
        "shared PE verifier differs",
    )
    spec = importlib.util.spec_from_file_location("edge_order_pe", path)
    require(
        spec is not None and spec.loader is not None,
        "shared PE verifier is unavailable",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = record["module"]
    image = module.Image(args.model, expected["sha256"])
    require(
        len(image.data) == expected["bytes"]
        and image.base == int(expected["base"], 16),
        "original module bounds differ",
    )
    for row in record["functions"]:
        image.verify_function(row)
    for row in record["instruction_windows"]:
        image.verify_span(row)
    for row in record["imports"]:
        require(
            image.imports()[row["iat"]]
            == {key: row[key] for key in ("module", "name")},
            "wire key primitive differs",
        )
    expected_immediates = record["immediates"]
    immediates = {}
    for row in expected_immediates:
        start = int(row["address"], 16)
        actual = unpack(row["format"], image.read(start, start + row["bytes"]))[0]
        require(actual == row["value"], "native initial-state or hash constant differs")
        immediates[row["name"]] = actual
    return {
        "functions": len(record["functions"]),
        "instruction_windows": len(record["instruction_windows"]),
        "imports": len(record["imports"]),
        "immediates": immediates,
    }


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "numeric output must be new")
    raw = args.record.read_bytes()
    record = json.loads(raw)
    require(
        record["schema"] == "kit.sw2026.downstream-edge-order-sources.v1"
        and record["archive_version"] == 19000,
        "source schema or version differs",
    )
    source = read_image(args, record)
    request_raw = sys.stdin.buffer.read()
    request = json.loads(request_raw)
    require(
        type(request) is dict and set(request) == {"keys", "wire_type"},
        "numeric request has unsupported members",
    )
    result = {
        "schema": "kit.sw2026.downstream-edge-order-pin.v1",
        "passed": True,
        "source_only": True,
        "tool_sha256": digest(Path(__file__).read_bytes()),
        "record_sha256": digest(raw),
        "request_sha256": digest(request_raw),
        "module_sha256": record["module"]["sha256"],
        "source_pin": source,
        "numeric": native_order(request["keys"], request["wire_type"]),
        "native_processes_started": 0,
        "generated_native_files": 0,
        "cad_inputs_read": 0,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
    }
    encoded = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(
        json.dumps(
            {
                "passed": True,
                "sha256": digest(encoded),
                "serialized_key_order": result["numeric"]["serialized_key_order"],
                "final_bucket_count": result["numeric"]["final_bucket_count"],
                "native_processes_started": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
