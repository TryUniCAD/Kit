from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Container.Container import SldprtArchive

PRIOR_RECEIPT = ROOT / "re/solidworks/measurements/2026/SdkDefaultPartNative01.json"
ROLES = ("Skew", "Step")


def digest(raw):
    return sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, expected):
    raw = path.read_bytes()
    require(digest(raw) == expected, "unexpected input digest: " + path.name)
    return raw


def write_json(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with path.open("xb") as output:
        output.write(raw)
    return digest(raw)


def candidate(captures, tag, role, filename):
    folder = captures / (tag + role)
    manifest_raw = (folder / "Candidate.json").read_bytes()
    manifest = json.loads(manifest_raw)
    require(
        manifest["stage"] == "awaiting_native_measurement"
        and manifest["runtime_input_reads"] == 0,
        "expected a guarded native candidate",
    )
    payload = checked(folder / filename, manifest["archive_sha256"])
    require(len(payload) == manifest["archive_bytes"], "candidate extent differs")
    return manifest, manifest_raw, payload


def records(raw):
    archive = SldprtArchive.from_bytes(raw)
    rows = {}
    for stream in archive.records:
        end = stream.payload_offset + stream.compressed_size
        compressed = raw[stream.payload_offset : end]
        rows[stream.name] = (
            [len(stream.data), digest(stream.data)],
            [len(compressed), digest(compressed)],
        )
    return (archive.file_id, archive.format_version), rows


def compare(captures, role, prior_value, filename):
    mac, _, original = candidate(captures, "Mac", role, filename)
    classic, _, windows = candidate(captures, "Windows", role, filename)
    current, first, generated = candidate(captures, "Windows314", role, filename)
    second, repeat, repeated = candidate(captures, "Windows314Repeat", role, filename)
    require(
        (mac, original) == (classic, windows)
        and (current, first, generated) == (second, repeat, repeated)
        and mac["archive_sha256"] == prior_value["candidate_sha256"],
        "cross-runtime anchor or independent regeneration differs",
    )
    props = ("native_locator", "written_at", "neutral_sha256", "streams")
    require(
        all(mac[key] == current[key] for key in props), "clear candidate streams differ"
    )
    old_format, old_records = records(original)
    new_format, new_records = records(generated)
    prior_streams = prior_value["streams"]
    require(
        old_format == new_format
        and list(old_records) == list(new_records)
        and len(old_records) == len(prior_streams) == 10,
        "container format or physical stream order differs",
    )
    proofs = {}
    for name, (clear, compressed) in old_records.items():
        measured = prior_streams[name]
        new_clear, new_compressed = new_records[name]
        require(
            clear
            == new_clear
            == current["streams"][name]
            == [measured["bytes"], measured["sha256"]]
            and measured["typed_roundtrip"]
            and compressed != new_compressed,
            "expected the exact typed stream and altered compression: " + name,
        )
        proofs[name] = {
            "clear": clear,
            "classic": compressed,
            "zlib_ng": new_compressed,
        }
    return current, first, generated, proofs


def stage(prior, captures, output):
    prior_evidence = json.loads(PRIOR_RECEIPT.read_bytes())
    prior_packet_raw = checked(prior / "Packet.json", prior_evidence["packet_sha256"])
    prior_packet = json.loads(prior_packet_raw)
    output.mkdir()
    tools = output / "Tools"
    tools.mkdir()
    for name, pin in prior_packet["tools"].items():
        (tools / name).write_bytes(checked(prior / "Tools" / name, pin))
    (output / "Control.SLDPRT").write_bytes((prior / "Control.SLDPRT").read_bytes())
    source_sha = digest((captures / "Kit235Code.zip").read_bytes())
    evidence = {
        "schema": "kit.sw2026.plain-part-compression-parity.v1",
        "source_package_sha256": source_sha,
        "runtime_package_sha256": digest(
            (captures / "python-3.14.10-embed-amd64.zip").read_bytes()
        ),
        "cases": [],
    }
    builds = []
    written_at = None
    require(
        tuple(row["role"] for row in prior_evidence["builds"]) == ROLES,
        "unexpected prior cases",
    )
    for row in prior_evidence["builds"]:
        role = row["role"]
        expected = checked(prior / role / "Expected.json", row["expected_sha256"])
        request = checked(prior / role / "SdkRequest.json", row["request_sha256"])
        locator = json.loads(request)["expected_locator"]
        filename = PureWindowsPath(locator).name
        current, manifest, raw, records_proof = compare(captures, role, row, filename)
        require(
            current["native_locator"] == locator
            and current["written_at"] == json.loads(request)["written_at"]
            and written_at in (None, current["written_at"]),
            "candidate locator or writer event differs",
        )
        written_at = current["written_at"]
        target = output / role
        target.mkdir()
        (target / "Expected.json").write_bytes(expected)
        (target / "SdkRequest.json").write_bytes(request)
        (target / filename).write_bytes(raw)
        builds.append(
            {
                **row,
                "candidate_sha256": current["archive_sha256"],
                "bytes": len(raw),
                "build_a_sha256": digest(manifest),
                "build_b_sha256": digest(manifest),
            }
        )
        evidence["cases"].append(
            {
                "role": role,
                "classic_sha256": row["candidate_sha256"],
                "classic_bytes": row["bytes"],
                "zlib_ng_sha256": current["archive_sha256"],
                "zlib_ng_bytes": len(raw),
                "streams": records_proof,
            }
        )
    proof = {
        "schema": "kit.sw2026.sdk-default-part-native.v2",
        "cases": builds,
        "written_at": written_at,
        "frozen_source_sha256": source_sha,
        "passed": True,
        "runtime_reads": 0,
        "heldout_inputs_read": 0,
    }
    packet = {
        "schema": proof["schema"],
        "oracle_sha256": prior_packet["oracle_sha256"],
        "heldout_inputs_read": 0,
        "tools": prior_packet["tools"],
        "build_proof_sha256": write_json(output / "BuildProof.json", proof),
    }
    evidence["packet_sha256"] = write_json(output / "Packet.json", packet)
    evidence["build_proof_sha256"] = packet["build_proof_sha256"]
    print(
        json.dumps(
            {
                "packet_sha256": evidence["packet_sha256"],
                "comparison_sha256": write_json(output / "Compression.json", evidence),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("prior", type=Path)
    parser.add_argument("captures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    stage(args.prior, args.captures, args.output)
