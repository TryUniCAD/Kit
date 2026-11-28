from pathlib import PurePosixPath
import json

from PatternParityPacket import BUILD, PRIOR_FREEZE, PRIOR_RESULT, SDK_REVISION, SLOTS, checked, require


TRIAL = "LinearPatternDefaultNative01"
PRIVATE = r"C:\KitLinearPatternDefaultNative01"
PARITY_MANIFEST = "cb2d03309afd69b3db52a620433f7a828a4a81618574fe6b5d73ad2a93f169fc"
PARITY_RESULT = "8ecbd2223e052e1e912a96c87cf50e79da5d6012c3a01617c83e45f3b89b923c"
SOURCE_LOCK = "3b35bab5c3f7d2b1b4dfcbb7d7eedfe132ae3ddc8c0a97eb91ba7d934c6a4c76"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SLOT = "Slot02"
SCHEMA = "kit.sw2026.oblique-pattern-default-native-packet.v1"
TOOLS = {"PatternParityPacket.py", "NativePatternPacket.py", "PatternLocatorLease.py", "RunPatternDefaultNative.py"}
ROLES = ("source-original", "source-spacing", "source-instances", "spacing-edit",
         "spacing-reopen", "instances-edit", "instances-reopen")


def divergent(raw):
    value = json.loads(raw)
    require(value["schema"] == "kit.sw2026.oblique-pattern-default-parity-result.v1" and value["completed"] is True
            and value["packet_sha256"] == PARITY_MANIFEST and value["prior_freeze_sha256"] == PRIOR_FREEZE
            and value["prior_result_sha256"] == PRIOR_RESULT and value["source_lock_sha256"] == SOURCE_LOCK
            and value["sdk_revision"] == SDK_REVISION and value["native_build"] == BUILD
            and value["prior_artifacts_immutable"] is value["private_data_guest_only"] is True
            and value["native_processes_started"] == 0 and value["matching_cases"] == value["different_cases"] == 1
            and tuple(row["slot"] for row in value["cases"]) == SLOTS,
            "redacted parity result does not select one exact locked divergence")
    equal, different = value["cases"]
    require(equal["byte_equal"] is True and different["byte_equal"] is False and different["slot"] == SLOT
            and different["disposition"] == "byte-difference"
            and all(row["deterministic"] is True and row["runtime_file_reads"] == 0
                    and row["writer_processes"] == 2 and row["typed_replays_per_generation"] == 9
                    and row["stream_count"] == 10 and row["repeat_sha256"] == row["generated_sha256"]
                    for row in value["cases"])
            and different["generated_sha256"] != different["prior_native_sha256"]
            and different["generated_bytes"] == different["prior_native_bytes"] > 0,
            "redacted output is ambiguous or has no repeatable divergence")
    return {key: different[key] for key in ("slot", "generated_sha256", "generated_bytes", "prior_native_sha256")}


def verified(packet, pin):
    data = json.loads(checked(packet / "Manifest.json", pin))
    require(packet.name == "Packet" and packet.parent.name == TRIAL and data["schema"] == SCHEMA
            and data["parity_manifest_sha256"] == PARITY_MANIFEST and data["parity_result_sha256"] == PARITY_RESULT
            and data["source_lock_sha256"] == SOURCE_LOCK and data["prior_freeze_sha256"] == PRIOR_FREEZE
            and data["prior_result_sha256"] == PRIOR_RESULT and data["sdk_revision"] == SDK_REVISION
            and data["phase_roles"] == list(ROLES) and data["native_build"] == BUILD and data["oracle_sha256"] == ORACLE
            and data["scope"]["slot"] == SLOT and data["expected_distinct_processes"] == 11,
            "unexpected qualified native packet manifest")
    paths = {"Tools/" + name for name in TOOLS}
    require(set(data["files"]) == paths and {path.relative_to(packet).as_posix() for path in packet.rglob("*")
                                             if path.is_file()} == paths | {"Manifest.json"},
            "native comparator code closure changed")
    for name, identity in data["files"].items():
        path = packet.joinpath(*PurePosixPath(name).parts)
        require(path.resolve(strict=True).is_relative_to(packet), "native comparator code escaped its packet")
        checked(path, identity)
    return data
