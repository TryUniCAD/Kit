# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Supervisor.Pilot.Metrics.PilotClient import WriteRecord


# empty independent attestations can establish zero observations without fabricating accepted documents
def EvidenceFiles(
    RootPath: FilePath, Window: dict[str, object]
) -> tuple[FilePath, str]:
    InputPins = {}
    for SourceName, FileName, Authority in (
        ("interventions", "Interventions.json", "operator_attestation"),
        ("agent_activity", "AgentIntervals.json", "measured_agent_intervals"),
        ("acceptance", "Acceptances.json", "independent_acceptance_attestation"),
    ):
        InputPins[SourceName] = WriteRecord(
            RootPath / FileName, {"version": 1, "authority": Authority, "records": []}
        )
    ManifestFile = RootPath / "PilotEvidence.json"
    ManifestHash = WriteRecord(
        ManifestFile, {"version": 1, "window": Window, "sources": InputPins}
    )
    return ManifestFile, ManifestHash
