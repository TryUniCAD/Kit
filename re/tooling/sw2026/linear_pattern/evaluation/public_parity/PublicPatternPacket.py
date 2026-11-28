from pathlib import PurePosixPath
import json
import os

from PatternParityPacket import (
    BUILD, PRIOR_FREEZE, PRIOR_RESULT, SDK_REVISION as BASE_REVISION, SLOTS,
    checked, require, safe_python, unpack_sources,
)


TRIAL = "LinearPatternPublicParity01"
PRIVATE = r"C:\KitLinearPatternPublicParity01"
SDK_REVISION = "41ee633c85336eba196e1579834e1dd871cc17b7"
SDK_TREE = "74c2e0ab3d6fecd2294c8b37902b2b4c019f5992"
BASE_MANIFEST = "cb2d03309afd69b3db52a620433f7a828a4a81618574fe6b5d73ad2a93f169fc"
BASE_RESULT = "8ecbd2223e052e1e912a96c87cf50e79da5d6012c3a01617c83e45f3b89b923c"
BASE_ZIP = "1e63e840eb3eb1df61b8cd2ea936b487154dd840792a90785c5ef4670f6c3c2d"
SOURCE_LOCK = "3b35bab5c3f7d2b1b4dfcbb7d7eedfe132ae3ddc8c0a97eb91ba7d934c6a4c76"
WORKER = "re/tooling/sw2026/linear_pattern/evaluation/public_parity/PublicPatternWorker.py"
SCHEMA = "kit.sw2026.public-oblique-pattern-parity-packet.v1"
PACKET_FILES = {"Overlay.zip", "Tools/PatternParityPacket.py", "Tools/PublicPatternPacket.py",
                "Tools/RunPublicPatternParity.py"}


def frozen_slots(raw):
    value = json.loads(raw)
    require(value["schema"] == "kit.sw2026.oblique-pattern-default-parity-result.v1" and value["completed"] is True
            and value["packet_sha256"] == BASE_MANIFEST and value["prior_freeze_sha256"] == PRIOR_FREEZE
            and value["prior_result_sha256"] == PRIOR_RESULT and value["source_lock_sha256"] == SOURCE_LOCK
            and value["sdk_revision"] == BASE_REVISION and value["native_build"] == BUILD
            and value["prior_artifacts_immutable"] is value["private_data_guest_only"] is True
            and value["matching_cases"] == value["different_cases"] == 1 and value["native_processes_started"] == 0
            and tuple(row["slot"] for row in value["cases"]) == SLOTS, "missing exact two-slot default parity authority")
    slots = {}
    for row in value["cases"]:
        require(row["deterministic"] is True and row["repeat_sha256"] == row["generated_sha256"]
                and row["generated_bytes"] > 0 and row["runtime_file_reads"] == 0
                and row["stream_count"] == 10 and row["typed_replays_per_generation"] == 9,
                "previous protected outputs were not generated twice under the exact purity guard")
        slots[row["slot"]] = {"sha256": row["generated_sha256"], "bytes": row["generated_bytes"]}
    return slots


def verified(packet, pin):
    data = json.loads(checked(packet / "Manifest.json", pin))
    require(packet.name == "Packet" and packet.parent.name == TRIAL and data["schema"] == SCHEMA
            and data["sdk_revision"] == SDK_REVISION and data["sdk_source_tree"] == SDK_TREE
            and data["parity_manifest_sha256"] == BASE_MANIFEST and data["parity_result_sha256"] == BASE_RESULT
            and data["base_source_zip_sha256"] == BASE_ZIP and data["source_lock_sha256"] == SOURCE_LOCK
            and list(data["slots"]) == list(SLOTS), "unexpected SDK overlay evidence")
    members = data["overlay_members"]
    require(WORKER in members and all(name == WORKER or name.startswith("src/") for name in members)
            and len({name.casefold() for name in members}) == len(members), "out-of-scope overlay source member")
    for name in members:
        safe_python(name)
    require(set(data["files"]) == PACKET_FILES and {path.relative_to(packet).as_posix()
            for path in packet.rglob("*") if path.is_file()} == PACKET_FILES | {"Manifest.json"},
            "public SDK proof code closure changed")
    for name, identity in data["files"].items():
        target = packet.joinpath(*PurePosixPath(name).parts)
        require(target.resolve(strict=True).is_relative_to(packet), "outside public proof packet")
        checked(target, identity)
    return data


def install_overlay(base_packet, base_manifest, overlay, members, home):
    original = base_manifest["source_members"]
    names = original.keys() | members.keys()
    require(len(names) == len({name.casefold() for name in names}), "overlay has Windows path aliases")
    require(base_manifest["packet_files"]["Source.zip"]["sha256"] == BASE_ZIP,
            "overlay requires the exact original parity source ZIP")
    code, update = home / "Code", home / "Overlay"
    unpack_sources(checked(base_packet / "Source.zip", BASE_ZIP), original, code)
    unpack_sources(overlay, members, update)
    for name, pin in members.items():
        relative = safe_python(name)
        source, target = update.joinpath(*relative.parts), code.joinpath(*relative.parts)
        checked(source, pin)
        if name in original:
            checked(target, original[name])
        else:
            require(not target.exists(), "new overlay member collides with existing source")
        target.parent.mkdir(parents=True, exist_ok=True)
        require(target.parent.resolve(strict=True).is_relative_to(code.resolve(strict=True)),
                "overlay destination escapes its fresh code root")
        os.replace(source, target)
        checked(target, pin)
    return code.joinpath(*safe_python(WORKER).parts)
