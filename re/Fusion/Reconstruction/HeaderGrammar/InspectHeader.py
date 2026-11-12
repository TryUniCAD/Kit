import hashlib
import json
from pathlib import Path
import subprocess


bundle = Path("/Users/odin/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents/Libraries/Neutron")
scratch = Path("/tmp/kit-fusion-native-analysis")
images = []
for name, intervals in (
    ("NsDataModel10", (("save_header", 0x25f544, 0x25f6b0), ("load_saved_version", 0x25ffd8, 0x260034), ("ancestry_lookup", 0x268158, 0x268198))),
    ("NsBaseCore10", (("version_constructor", 0x12cac4, 0x12caf4), ("version_accessors", 0x12cc88, 0x12cd38))),
):
    original = bundle / (name + ".dylib")
    thin = scratch / (name + ".arm64.dylib")
    if not thin.exists():
        subprocess.run(["lipo", "-thin", "arm64", str(original), "-output", str(thin)], check=True)
    excerpts = []
    for label, start, end in intervals:
        command = ["xcrun", "llvm-objdump", "--disassemble", "--demangle", "--start-address=" + hex(start), "--stop-address=" + hex(end), str(thin)]
        excerpts.append({"name": label, "start": hex(start), "end": hex(end), "disassembly": subprocess.check_output(command, text=True).splitlines()})
    images.append({"image": name + ".dylib", "image_sha256": hashlib.sha256(original.read_bytes()).hexdigest(), "thin_sha256": hashlib.sha256(thin.read_bytes()).hexdigest(), "architecture": "arm64", "address_basis": "Unslid Mach-O virtual address, not universal file offset", "excerpts": excerpts})
packed = (2706 << 50) | (1 << 38) | 17
report = {
    "scope": "Static native metadata header interpretation; no library loaded or native code invoked",
    "saved_version": {"major_bits": 14, "minor_bits": 12, "build_input_bits": 32, "unused_bits": [32, 37], "formula": "(major << 50) | (minor << 38) | build", "controlled_version": [2706, 1, 17], "packed_hex": hex(packed), "legacy_two_u32_view": [packed & 0xffffffff, packed >> 32]},
    "header_roles": {"namespace_uuid": "SegmentImpl.currentVersion", "magic": "Literal 1234 emitted by SegmentBinaryMetaStreamer.save", "header_words": "One little-endian u64 lastSavedSoftwareVersion", "storage_space": "SegmentType.addIn", "storage_word_first": "SegmentType.neutronType enum", "storage_word_second": "Count of inherited segment version UUIDs, followed by that many UTF-16 UUID strings", "ancestry_evidence": "The same SegmentImpl vector at +0xa8 is emitted by save and scanned by isDescendedFrom"},
    "qualification": "Current production framing admits only the observed zero-ancestry profile; this evidence does not qualify older metadata versions or nonempty ancestry runtime acceptance",
    "images": images,
}
Path(__file__).with_name("NativeHeader.json").write_text(json.dumps(report, indent=2) + "\n")
