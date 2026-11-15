"""Compare a vendor CATPart with the writer's output for the same decoded model.

Decode a corpus part, write it back through the native writer, and print both streams' sizes and
`00 33 <kind>` record counts. This is a structural fidelity check, not a vendor check: it says how
close the writer's bytes are to the file it came from, which is what a round trip through our own
reader cannot show.

Usage: uv run python re/catia/tooling/Transcode.py [name ...]
"""

from __future__ import annotations

import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")

from convert.adapters import WriteOptions
from convert.adapters.catia.Adapter import CatiaAdapter
from convert.adapters.catia.Container import CfvTwoArchive
from convert.adapters.catia.NativeBrep import DecodeBrep, Largest
from interchange import Body, CadDocument, CadSource

KBase = Path("re/catia/examples/.CATPart")


def Kinds(Data: bytes) -> Counter[int]:
    """Count the `00 33 <kind>` surface and curve records in a stream."""
    Found: Counter[int] = Counter()
    for Offset in range(len(Data) - 2):
        if Data[Offset : Offset + 2] == b"\x00\x33":
            Found[Data[Offset + 2]] += 1
    return Found


def Streams(PathValue: Path) -> tuple[bytes, bytes]:
    """Return the MainDataStream and SurfacicReps bytes of a CATPart."""
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Folder = Archive.nested[0]
    return (
        Archive.stream_bytes(Largest(Folder, "MainDataStream"), Folder),
        Archive.stream_bytes(Largest(Folder, "SurfacicReps"), Folder),
    )


def Compare(Name: str) -> None:
    """Report one part's vendor and written stream statistics."""
    Source = KBase / f"{Name}.CATPart"
    Model, _ = DecodeBrep(CfvTwoArchive.from_bytes(Source.read_bytes()))
    if Model is None:
        print(f"{Name}: decode failed")
        return
    Document = CadDocument(
        source=CadSource("catia.v5", Source.name, "0" * 64),
        configurations=(),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(Body("catia:body:1", Name, ""),),
        brep=Model,
    )
    Output = Path(tempfile.mkdtemp()) / Source.name
    CatiaAdapter().write(
        Document, Output, WriteOptions(validate=False, values={"native_brep": True})
    )
    VendorMain, VendorSurf = Streams(Source)
    MineMain, MineSurf = Streams(Output)
    print(
        f"{Name}: faces {len(Model.faces)} edges {len(Model.edges)}"
        f" | main {len(VendorMain)} -> {len(MineMain)}"
        f" | surf {len(VendorSurf)} -> {len(MineSurf)}"
    )
    print(f"  vendor records {dict(sorted(Kinds(VendorSurf).items()))}")
    print(f"  written records {dict(sorted(Kinds(MineSurf).items()))}")


def Main() -> None:
    """Compare the named parts, or the whole corpus."""
    Names = sys.argv[1:] or ["Copper_Washer", "Washer_8", "Nut_M6", "BRK_PRS_Sensor"]
    for Name in Names:
        Compare(Name)


if __name__ == "__main__":
    Main()
