from __future__ import annotations

from tools.TestShards.PhaseReport import PhaseReport

# severity order lets the worst phase decide how a test appears in the summary
KOutcomeRanks = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}


# fixture failures are reported as errors so summaries match the pytest terminal wording
def MergeOutcome(Current: str | None, PhaseInfo: PhaseReport) -> str:
    Candidate = PhaseInfo.Outcome
    if Candidate == "failed" and PhaseInfo.Phase != "call":
        Candidate = "error"
    if Current is None or KOutcomeRanks.get(Candidate, 3) > KOutcomeRanks.get(
        Current, 3
    ):
        return Candidate
    return Current
