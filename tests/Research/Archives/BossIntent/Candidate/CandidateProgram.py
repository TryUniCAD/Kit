from tests.Research.Archives.BossIntent.Candidate.RequestAudit import KRequestAudit
from tests.Research.Archives.BossIntent.Candidate.RequestReplay import KRequestReplay
from tests.Research.Archives.BossIntent.Candidate.RequestSetup import KRequestSetup
from tests.Research.Archives.SolidWorksFreshBossTests import (
    KPortContext,
    KPortGraph,
    KPortImports,
    KPortWires,
)

# the replay audit must precede project imports and every constructor context stage
KRequestProgram = (
    KRequestSetup
    + KRequestAudit
    + KPortImports
    + KPortGraph
    + KPortWires
    + KPortContext
    + KRequestReplay
)
