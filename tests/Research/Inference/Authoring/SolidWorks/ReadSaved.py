# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import loads
from pathlib import Path
from sys import argv, path

# the child must load the checkout being tested instead of an installed sdk
KSourceRoot = Path(__file__).resolve().parents[5]

path.insert(0, str(KSourceRoot / "re/automation"))

from CaptureTools.Catalogue.SolidWorks.CheckSolidShape import CheckSolidShape
from CaptureTools.Catalogue.SolidWorks.ValidateSolid import ValidateSolid


# retained native controls exercise the real measurement reader without repeating licensed authoring
def ReadSaved() -> None:
    RecipeKey = argv[1]
    Paths = list(
        (KSourceRoot / "re/automation/PairedCaptures" / RecipeKey).glob(
            "solidworks-*/measurements.json"
        )
    )
    if len(Paths) != 1:
        raise ValueError("expected exactly one retained native measurement report")
    ReportPath = Paths[0]
    ReportBytes = ReportPath.read_bytes()
    Receipt = loads(ReportPath.with_name("receipt.json").read_bytes())
    if Receipt["measurement_receipt_sha256"] != sha256(ReportBytes).hexdigest():
        raise ValueError("retained native measurement bytes differ from their receipt")
    Observed = loads(ReportBytes)["observations"]
    CaseValue = ValidateSolid({"recipe": RecipeKey})
    for StageName in ("baseline", "unchanged_rebuild"):
        CheckSolidShape(CaseValue, Observed[StageName])
    print(RecipeKey + " retained native geometry matched")


if __name__ == "__main__":
    ReadSaved()
