import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path


RANGES = {
    "Libraries/Applications/Fusion/FusionXLayer10.dylib": [
        ("temporary_brep_extension_dispatch_and_units", 0x168B00, 0x168EC4),
    ],
    "Libraries/Neutron/XLayer10.dylib": [
        ("smt_import_extension_validation", 0xB0060, 0xB00F4),
    ],
    "Libraries/Neutron/NsASMInterface10.dylib": [
        ("restore_mode_selection", 0x4997C, 0x49BE0),
        ("smb_file_restore", 0x4AC4C, 0x4AD08),
    ],
    "Frameworks/ASM/libASMkern232.dylib": [
        ("binary_header_write", 0x53DC10, 0x53DE18),
        ("binary_header_recognition", 0x53DEAC, 0x53E0D8),
        ("binary_integer_width_and_range", 0x53C670, 0x53C7C8),
        ("text_or_binary_file_selection", 0x1A9054, 0x1A9108),
        ("header_version_decode", 0x1A7D64, 0x1A7D80),
        ("header_root_assembly", 0x1A81E4, 0x1A8240),
        ("header_count_and_flags_write", 0x1A8478, 0x1A868C),
        ("header_restore", 0x1AA4D8, 0x1AA628),
        ("metadata_strings_write", 0x1A6C78, 0x1A6D1C),
        ("metadata_numbers_write", 0x1A6DBC, 0x1A6DDC),
        ("metadata_restore", 0x1A6F84, 0x1A7030),
        ("ordinary_save_history_argument", 0x1A7FE0, 0x1A800C),
        ("history_save_history_argument", 0x62C7F8, 0x62C818),
    ],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect_images(contents):
    images = []
    for relative, ranges in RANGES.items():
        path = contents / relative
        data = path.read_bytes()
        result = subprocess.run(
            ["otool", "-arch", "arm64", "-tvV", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        instructions = []
        for line in result.stdout.splitlines():
            try:
                address = int(line[:16], 16)
            except ValueError:
                continue
            instructions.append((address, line))
        images.append({
            "image": relative,
            "sha256": digest(data),
            "architecture": "arm64",
            "address_basis": "Mach-O slice virtual address before runtime slide",
            "excerpts": [
                {
                    "name": name,
                    "start_inclusive": hex(start),
                    "end_exclusive": hex(end),
                    "instructions": [line for address, line in instructions if start <= address < end],
                }
                for name, start, end in ranges
            ],
        })
    return images


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("contents", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("acceptance", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    candidate = arguments.candidate.read_bytes()
    acceptance_bytes = arguments.acceptance.read_bytes()
    acceptance = json.loads(acceptance_bytes)
    width = int(chr(candidate[14]))
    words = struct.unpack_from("<4" + ("q" if width == 8 else "i"), candidate, 15)
    report = {
        "scope": "Static inspection only; no product code, native function or test executed by this script",
        "candidate": {
            "path": str(arguments.candidate),
            "sha256": digest(candidate),
            "bytes": len(candidate),
            "magic": candidate[:15].decode("ascii"),
            "integer_width": width,
            "header": dict(zip(("save_format", "stored_record_count", "top_level_entity_count", "flags"), words)),
        },
        "parent_native_acceptance": {
            "path": str(arguments.acceptance),
            "report_sha256": digest(acceptance_bytes),
            "report": acceptance,
        },
        "images": inspect_images(arguments.contents),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"output": str(arguments.output), "images": len(report["images"]), "candidate_sha256": digest(candidate)}))


if __name__ == "__main__":
    main()
