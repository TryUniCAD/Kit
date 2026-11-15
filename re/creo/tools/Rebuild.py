"""Research probe: rebuild the 47-row generative part from the committed writer.

The retained empty control contributes only its directory skeleton and the six rows the writer cannot yet
generate. Every other row comes from `convert.adapters.creo.Author`, and the result loads in Creo 2027.2 with
`End` and `MT Part Solid` and no `dbg_err_crash`.

This exists so the claim is reproducible with one command rather than by replaying a transcript:

    PYTHONPATH=src python3 re/creo/tools/Rebuild.py

The generated file is written to `~/Documents/creo-authored/gen_rows.prt`. It is a research artifact built on a
vendor control container and is never shipped.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo import Author
from convert.adapters.creo.Header import ReadHeader

KControl = Path("re/creo/oracle/empty/solid_start_part_mmks.prt")
KFeatureClasses = (923, 979, 917)


def Build(Source: Path, Target: Path) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Bodies = Author.EmptyPartSections(KFeatureClasses)
    Bodies["VisibGeom"] = Author.EmptyVisibGeom()
    Replace = {
        NameText: Author.SectionValue(
            NameText, Author.StripSectionHeader(NameText, Payload)
        )
        for NameText, Payload in Bodies.items()
    }
    Result = Subset.Build(DataValue, Header.base, set(), Replace)
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes, {len(Replace)} generated rows")
    return Result


if __name__ == "__main__":
    Build(KControl, Path.home() / "Documents/creo-authored/gen_rows.prt")
