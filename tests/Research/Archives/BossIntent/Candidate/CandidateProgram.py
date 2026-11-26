from tests.Research.Archives.SolidWorksFreshBossTests import (
    KPortContext,
    KPortGraph,
    KPortImports,
    KPortWires,
)

# isolated execution must resolve the exact checkout rather than installed or ambient modules
KRequestSetup = """
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path[:0] = [str(root / "src"), str(root),
    str(root / "re/automation"), str(root / "re/solidworks/WriterResearch")]
"""

# opening another model input would invalidate the source free request replay evidence
KRequestAudit = """
from P03CandidateRequest import generate_request
request_path = Path(sys.argv[2]).resolve()
allowed = {str(request_path),
    str((root / "src/convert/adapters/solidworks/Config/RootLayout.json").resolve())}
observed_reads = set()
def audit_model_reads(event, arguments):
    if event == "open" and isinstance(arguments[0], (str, bytes)):
        selected = Path(arguments[0]).resolve()
        if selected.suffix.lower() in (".json", ".sldprt", ".f3d"):
            assert str(selected) in allowed, str(selected)
            observed_reads.add(str(selected))
sys.addaudithook(audit_model_reads)
payload = request_path.read_bytes()
report = generate_request(payload, sys.argv[3], context, candidate=None)
print(json.dumps({"result": report, "model_reads": sorted(observed_reads)}))
"""

# reuse the proven authored fixture composition while changing only the actual request consumer
KRequestProgram = (
    KRequestSetup
    + KPortImports
    + KPortGraph
    + KPortWires
    + KPortContext
    + KRequestAudit
)
