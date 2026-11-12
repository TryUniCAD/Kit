import json
import runpy
from pathlib import Path


BASE = Path(__file__).resolve().parent
TOOLS = runpy.run_path(str(BASE.parent / "OgsScene/InspectSerializers.py"))


def main():
    relative = "Libraries/Neutron/NsScene10.dylib"
    binary = TOOLS["API"]["Binary"](TOOLS["APP"] / relative)
    targets = [name for name in binary.named if "FusionGroupNodeSerializer::SerializeParameshBody(" in name or "FusionGroupNodeSerializer::DeSerializeParameshBody(" in name]
    report = {
        "scope": "Static symbol and call-site inspection; no native library execution or claimed complete mesh-world grammar",
        "application_version": "2706.1.17", "architecture": "arm64",
        "address_basis": "Unslid Mach-O virtual address", "image": relative,
        "image_sha256": binary.sha256,
        "methods": [TOOLS["inspect"](binary, name) for name in targets],
    }
    (BASE / "MeshWorldEvidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
