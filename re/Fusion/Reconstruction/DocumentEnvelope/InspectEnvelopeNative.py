import argparse
import hashlib
import json
import subprocess
from pathlib import Path


RANGES = {
    "Libraries/Neutron/NsScene10.dylib": [
        ("OGSBlobSerializer::doLoad optional persistence and folder", 0x2b8890, 0x2b8910),
        ("OGSBlobSerializer::doLoad null return", 0x2b8c4c, 0x2b8c7c),
        ("OGSSerializer::IsPersistOGS", 0x2b9b88, 0x2b9b9c),
        ("OGSSerializer::prepareBlobPreAssetSave", 0x2b9c14, 0x2b9d6c),
        ("OGSSerializer::syncToBlobAfterLoad", 0x2ba7a0, 0x2ba89c),
        ("OGSSerializer::postActivate null branch", 0x2ba8cc, 0x2ba8f8),
        ("OGSSerializer::postActivate return", 0x2bacec, 0x2bad0c),
    ],
    "Libraries/libadskassetapi_new-16.dylib": [
        ("DataStoreRecord::size", 0xaf928, 0xafa1c),
        ("DataStoreRecord::read", 0xafb3c, 0xafcac),
        ("DataStore::initBlock_", 0xb1110, 0xb1200),
        ("GeneralLibrary::loadAndConstructProperties_ start", 0xc78e4, 0xc7bdc),
        ("GeneralLibrary::writeTableOfContents_", 0xc9be0, 0xca374),
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("contents", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    images = []
    for relative, ranges in RANGES.items():
        path = arguments.contents / relative
        result = subprocess.run(["otool", "-arch", "arm64", "-tvV", str(path)], capture_output=True, text=True, check=True)
        instructions = []
        for line in result.stdout.splitlines():
            try:
                address = int(line[:16], 16)
            except ValueError:
                continue
            instructions.append((address, line))
        images.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "excerpts": [{"name": name, "start": hex(start), "end_exclusive": hex(end), "instructions": [line for address, line in instructions if start <= address < end]} for name, start, end in ranges]})
    report = {"scope": "Static disassembly only; no library loading or native calls", "architecture": "arm64", "address_basis": "Mach-O slice virtual address before runtime slide", "images": images}
    with arguments.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
