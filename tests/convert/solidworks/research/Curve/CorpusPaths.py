from __future__ import annotations

from tests.convert.solidworks.research.ArchiveProcess import KRepoRoot
from tests.convert.solidworks.research.ArchiveRoundTests import KStreams

# discovery fixtures expose native parser coverage without opening sealed held out payloads
KCurveCorpus = KRepoRoot / "re/solidworks/v2026/corpus/curves-discovery"

# the original lock prevents public fixture membership from silently changing splits
KCurveLock = KRepoRoot / "re/solidworks/v2026/heldout/CurveSourceLock.json"

# owner verification anchors prepared fixtures to the independently measured source family
KSourceProof = KRepoRoot / "re/solidworks/measurements/2026/CurveSourceLock02.json"

# the display header must preserve bytes alongside every critical archive stream
KPrimaryStreams = (*KStreams, "Header2")
