import hashlib
import json
import runpy
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FOLDER = Path(__file__).resolve().parent
SOURCE = ROOT / "re/Fusion/Study/extents-f0f33a9a605f/taper.f3d"
NATIVE = Path("/Users/odin/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents/Helpers/AcCoreConsole.app/Contents/Frameworks/libASMkern232.dylib")
THIN = Path("/tmp/kit-fusion-native-analysis/ASMkern232.arm64.dylib")
READER = runpy.run_path(str(ROOT / "re/Fusion/Reconstruction/BrepTokens.py"))["read_stream"]


def main():
    ground_path = SOURCE.parent / "ground_truth.json"
    ground = json.loads(ground_path.read_text())
    sample = next(row for row in ground["samples"] if row["file"] == "taper.f3d")
    with zipfile.ZipFile(SOURCE) as archive:
        member = next(name for name in archive.namelist() if name.endswith(".smbh"))
        data = archive.read(member)
    parsed = READER(data)
    selected = []
    for row in parsed["records"]:
        if row["boundary_marker"]:
            break
        if row["name"] in ("cone-surface", "ellipse-curve", "plane-surface", "point", "edge", "vertex"):
            selected.append(row)
    slices = []
    for name, start, stop in (
        ("cone::save_data", 0x439430, 0x4394d8),
        ("cone::restore_data", 0x43958c, 0x439650),
        ("cone::eval", 0x437028, 0x437204),
        ("cone::get_apex", 0x435838, 0x4358e8),
    ):
        output = subprocess.check_output([
            "xcrun", "llvm-objdump", "--disassemble", "--demangle",
            f"--start-address={start:#x}", f"--stop-address={stop:#x}", str(THIN),
        ], text=True)
        slices.append({"symbol": name, "start": hex(start), "stop": hex(stop), "disassembly": output})
    report = {
        "scope": "Read-only native binary/source-data inspection; no runtime calls or product execution",
        "source": str(SOURCE.relative_to(ROOT)),
        "sourceSha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "groundTruthSha256": hashlib.sha256(ground_path.read_bytes()).hexdigest(),
        "groundTruth": sample,
        "member": member,
        "memberSha256": hashlib.sha256(data).hexdigest(),
        "header": parsed["header"],
        "records": selected,
        "nativeBinary": str(NATIVE),
        "nativeBinarySha256": hashlib.sha256(NATIVE.read_bytes()).hexdigest(),
        "thinSha256": hashlib.sha256(THIN.read_bytes()).hexdigest(),
        "disassembly": slices,
        "importStubs": {
            "0xa25760": "___sincos_stret (verified by llvm-objdump --macho --indirect-symbols)",
            "0xa2438c": "ASM::operator-(ASM::position const&, ASM::vector const&)",
        },
        "objectFields": {
            "0x40": "embedded ellipse object",
            "0x60": "ellipse center (three doubles)",
            "0x78": "ellipse unit axis (three doubles)",
            "0x90": "ellipse major vector (three doubles)",
            "0xa8": "ellipse axis ratio",
            "0xb0": "signed sine of cone semi-angle",
            "0xb8": "cosine of cone semi-angle",
            "0xc0": "longitudinal parameter scale (length)",
            "0xc8": "sense boolean",
        },
        "canonicalEquation": "p(u,v)=base+(rb+u*scale*sinAngle)*(cos(v),sin(v),0)+(0,0,u*scale*cosAngle); circular forward cone, cosine positive",
        "authoredParameters": {
            "deltaRadius": "rt-rb", "slant": "hypot(height,rt-rb)",
            "sinAngle": "(rt-rb)/slant", "cosAngle": "height/slant", "scale": "rb",
            "upperU": "height/(rb*cosAngle)", "radialLaw": "r(z)=rb+z*sinAngle/cosAngle",
        },
        "upstream": {
            "url": "https://github.com/jmplonka/InventorLoader/blob/master/Acis.py",
            "class": "SurfaceCone", "lines": [2767, 2828],
            "corroboration": "Parser independently names sine/cosine and reads the following field as length; its apex reconstruction agrees with center-axis*radius*cosine/sine",
            "codeCopied": False,
        },
        "limits": [
            "Native binary save-version comparisons use internal version numbers; this report does not equate those directly with SMB header 23200",
            "Canonical circular forward cone only; reversed sense, negative cosine, ellipse ratio not one and bounded UV ranges are not implemented",
            "Topology construction is independent; native taper happens to serialize the upper ellipse with axis -Z, while the authored loops use +Z with complementary coedge senses",
            "No apex: both authored cap radii are strictly positive",
        ],
    }
    (FOLDER / "ConeEvidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("source", "sourceSha256", "memberSha256", "nativeBinarySha256")}))


if __name__ == "__main__":
    main()
