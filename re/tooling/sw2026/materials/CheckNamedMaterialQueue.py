from hashlib import sha256
from io import BytesIO
from json import dumps
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from convert import open_document
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive


def check():
    data = (ROOT / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT").read_bytes()
    if sha256(data).hexdigest() != "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6":
        raise ValueError("unassigned part fixture changed")
    archive = SldprtArchive.from_bytes(data)
    name = "swXmlContents/MATERIALTREE"
    if name in archive.streams:
        raise ValueError("unassigned part acquired a material stream")
    contrast = BuildSldprt(dict(archive.streams) | {name: b"unsupported material evidence"},
                           FormatVersion=archive.format_version)
    results = {}
    for mode, include_brep in (("design", False), ("geometry", True)):
        options = dict(source_format="solidworks.sldprt", strict=True, include_brep=include_brep)
        control = open_document(BytesIO(data), **options)
        rejected = open_document(BytesIO(contrast), **options)
        if (control.materials or rejected.materials or control.bodies != rejected.bodies
                or control.feature_timeline != rejected.feature_timeline or control.brep != rejected.brep
                or any("solidworks.assigned_part_material" in row.attributes for row in rejected.bodies)
                or (control.brep is not None) != include_brep
                or any(row.code.startswith("sldprt.material_") for row in control.diagnostics)):
            raise ValueError("material evidence changed unassigned semantics")
        outcome, = (row for row in rejected.diagnostics if row.code == "sldprt.material_assignment_unresolved")
        expected = "SOLIDWORKS assigned material density is absent, overridden or inconsistent"
        if outcome.message != expected:
            raise ValueError("unexpected reason to decline unowned material")
        results[mode] = outcome.message
    return results


if __name__ == "__main__":
    print(dumps(check(), sort_keys=True))
