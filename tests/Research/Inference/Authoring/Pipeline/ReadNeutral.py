# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from sys import argv, path, stdout

path.insert(0, str(Path(__file__).resolve().parents[5] / "src"))

from convert import open_document


# a fresh public reader process supplies the actual neutral bytes for retained evidence comparison
def ReadNeutral() -> None:
    Document = open_document(
        Path(argv[1]).read_bytes(),
        source_format="fusion.f3d",
        strict=False,
        include_brep=False,
        include_tessellation=False,
    )
    _ = stdout.write(Document.to_json(indent=None))


if __name__ == "__main__":
    ReadNeutral()
