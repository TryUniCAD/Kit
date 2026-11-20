# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from pathlib import Path as FilePath
from subprocess import check_output as ReadProcess


# both lanes remain explicit while the synthetic manifest deliberately supplies no native observations
def BuildManifest(RepoRoot: FilePath) -> dict[str, object]:
    Revision = ReadProcess(
        ["git", "-C", str(RepoRoot), "rev-parse", "HEAD"], text=True
    ).strip()
    return {
        "version": 1,
        "scope": "paired_supplemental_preflight",
        "target_revision": Revision,
        "capture_revision": Revision,
        "frozen_rules_revision": Revision,
        "specifications_sha256": DigestBytes(
            (RepoRoot / "re/automation/PairSpecs.json").read_bytes()
        ).hexdigest(),
        "recipes": ["P01"],
        "evidence": [
            {
                "application": Application,
                "recipe": "P01",
                "source_revision": Revision,
                "verifier_revision": Revision,
                "verifier_sha256": DigestBytes(
                    (RepoRoot / Verifier).read_bytes()
                ).hexdigest(),
                "input_directory": Application,
                "input_sha256": "a" * 64,
                "report_sha256": "b" * 64,
                **({"handoff_revision": Revision} if Application == "fusion" else {}),
            }
            for Application, Verifier in (
                ("solidworks", "re/automation/PrincipalReadbackEvidence.py"),
                (
                    "fusion",
                    "re/automation/CaptureTools/PairedCaptures/FusionRunEvidence.py",
                ),
            )
        ],
    }
