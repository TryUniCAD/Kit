from tests.Research.Archives.BossIntent.Candidate.RequestAudit import KRequestAudit
from tests.Research.Archives.BossIntent.Candidate.RequestReplay import KRequestReplay
from tests.Research.Archives.BossIntent.Candidate.RequestSetup import KRequestSetup
from tests.Research.Archives.SolidWorksFreshBossTests import (
    KPortContext,
    KPortGraph,
    KPortImports,
    KPortWires,
)

# reuse the proven authored fixture composition while changing only the actual request consumer
KRequestProgram = (
    KRequestSetup
    + KPortImports
    + KPortGraph
    + KPortWires
    + KPortContext
    + KRequestAudit
    + KRequestReplay
)
