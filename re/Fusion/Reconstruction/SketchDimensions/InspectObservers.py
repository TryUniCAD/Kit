import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import zipfile


sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / "DocumentEnvelope/ReadEnvelope.py"))
NATIVE = Path("/tmp/kit-fusion-native-analysis")
OBJDUMP = "/Library/Developer/CommandLineTools/usr/bin/llvm-objdump"
SOURCES = [
    "re/Fusion/LocalOracle/RectangleDimensions/" + name + ".f3d"
    for name in ("Baseline", "WidthDimension", "WidthDepthDimensions", "EditedDimensions")
] + ["re/Fusion/LocalOracle/Authored/ProductionExtrusion.f3d"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive_slots(relative):
    path = ROOT / relative
    segments = []
    with zipfile.ZipFile(path) as archive:
        for member in sorted(archive.namelist()):
            if not member.endswith("/MetaStream.dat"):
                continue
            bulk_name = member.removesuffix("MetaStream.dat") + "BulkStream.dat"
            if bulk_name not in archive.namelist():
                continue
            meta, bulk = archive.read(member), archive.read(bulk_name)
            graph = API["segment"](meta, bulk)
            if set(graph["status_counts"]) != {"decoded"}:
                raise ValueError("Observer inventory requires fully decoded segments")
            segments.append({"member": member, "metadataSha256": digest(meta), "bulkSha256": digest(bulk), "graph": graph})
    roots = [
        (entry["graph"]["header"]["segment_id"], record["identity"])
        for entry in segments for record in entry["graph"]["records"]
        if record["value"]["frame"].get("rootId") == "AssetSettings"
    ]
    if len(roots) != 1:
        raise ValueError("Exactly one AssetSettings root is required")
    subscribers = []
    for entry in segments:
        graph = entry["graph"]
        segment_id = graph["header"]["segment_id"]
        for record in graph["records"]:
            for subject in record["value"]["frame"].get("subjects", []):
                target = subject["subject"]
                if (target.get("segmentId", segment_id), target.get("entityId")) != roots[0]:
                    continue
                subscribers.append({
                    "observerSegmentId": segment_id, "observerEntityId": record["identity"],
                    "observerClass": record["class_name"], "observerClassId": record["class"]["identifier"],
                    "observerClassVersion": record["class"]["schemaVersion"],
                    "subject": target, "observerIndex": subject["indexInObserverVec"],
                })
        entry.update({"segmentId": segment_id, "kind": graph["header"]["kind"], "recordCount": len(graph["records"]), "statusCounts": graph["status_counts"]})
        del entry["graph"]
    slots = sorted({row["observerIndex"] for row in subscribers})
    return {
        "source": relative, "sourceSha256": digest(path.read_bytes()), "segments": segments,
        "settingsRoot": {"segmentId": roots[0][0], "entityId": roots[0][1]},
        "persistedSubscribers": sorted(subscribers, key=lambda row: row["observerIndex"]),
        "persistedSlots": slots, "unrepresentedSlotsBelowMaximum": sorted(set(range(max(slots) + 1)) - set(slots)),
    }


def native_slice(library, start, end):
    path = NATIVE / (library + ".arm64.dylib")
    text = subprocess.check_output([
        OBJDUMP, "--disassemble", "--demangle", "--start-address=" + start,
        "--stop-address=" + end, str(path),
    ], text=True)
    instructions = []
    for line in text.splitlines():
        match = re.match(r"\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+(.+)", line)
        if match:
            instructions.append({"address": "0x" + match[1], "assembly": match[2]})
    return {"library": library, "architecture": "arm64", "thinSha256": digest(path.read_bytes()), "start": start, "endExclusive": end, "instructions": instructions}


def native_evidence():
    ranges = [
        ("EntityObserversConstructor", "NsDataModel10", "0x3309b4", "0x3309ec"),
        ("UnindexedSubscribe", "NsDataModel10", "0x321e9c", "0x321ea4"),
        ("SharedObserverInsertion", "NsDataModel10", "0x32193c", "0x32196c"),
        ("EntitySubjectsRegistration", "NsDataModel10", "0x321b8c", "0x321bbc"),
        ("NonEntitySubjectsRegistration", "NsDataModel10", "0x321cd4", "0x321ce0"),
        ("AppendOrExplicitIndex", "NsDataModel10", "0x330fe4", "0x33108c"),
        ("SparseIndexPlaceholders", "NsDataModel10", "0x3310bc", "0x33112c"),
        ("LoaderCollisionResolution", "NsDataModel10", "0x322020", "0x322060"),
        ("SubjectIndexWriteback", "NsDataModel10", "0x33656c", "0x3365e4"),
        ("ObserverSaveUndoOnly", "NsDataModel10", "0x333428", "0x333454"),
        ("ObserverSaveNonEntityPlaceholder", "NsDataModel10", "0x3334c0", "0x333544"),
        ("DimensionSettingsSubscription", "NsDimension10", "0x2081c", "0x208d8"),
        ("SketchGeometrySubscription", "NaSketch10", "0x12cac4", "0x12cb40"),
    ]
    evidence = {name: native_slice(library, start, end) for name, library, start, end in ranges}
    imports = {}
    addresses = {"NsDimension10": {"0x29a4c", "0x29a58", "0x29b18", "0x2a208", "0x2a304", "0x2a628", "0x2a6ac", "0x2a6f4"}, "NaSketch10": {"0x265a04", "0x2644f8", "0x262944", "0x266940"}}
    for library, selected in addresses.items():
        text = subprocess.check_output([OBJDUMP, "--macho", "--indirect-symbols", str(NATIVE / (library + ".arm64.dylib"))], text=True)
        rows = []
        for line in text.splitlines():
            parts = line.split()
            if len(parts) != 3 or not parts[0].startswith("0x") or hex(int(parts[0], 16)) not in selected:
                continue
            symbol = subprocess.check_output(["c++filt", parts[2][1:]], text=True).strip()
            rows.append({"address": hex(int(parts[0], 16)), "symbol": symbol})
        imports[library] = rows
    catalog = json.loads((BASE.parent / "BinaryClasses.json").read_text())
    return {"schema": "FusionObserverNativeEvidence/1", "applicationVersion": catalog["applicationVersion"], "method": "Static disassembly of thin arm64 images only; no native calls or production execution", "sources": [row for row in catalog["sources"] if row["id"] in {"NsDataModel10", "NsDimension10", "NaSketch10"}], "functions": evidence, "importStubs": imports}


def main():
    slots = {"schema": "FusionSettingsObserverSlots/1", "method": "Research decoder reads all serialized entity segments and inventories AssetSettings subject frames", "decoderSha256": digest((BASE.parent / "DocumentEnvelope/ReadEnvelope.py").read_bytes()), "archives": [archive_slots(path) for path in SOURCES]}
    (BASE / "ObserverSlots.json").write_text(json.dumps(slots, indent=2) + "\n")
    evidence = native_evidence()
    (BASE / "ObserverNativeEvidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"archiveCount": len(slots["archives"]), "persistedSlots": {Path(row["source"]).stem: row["persistedSlots"] for row in slots["archives"]}, "nativeSections": len(evidence["functions"])}, indent=2))


if __name__ == "__main__":
    main()
