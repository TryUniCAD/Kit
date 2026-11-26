import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import SessionHost


# owner replacement checks need to pause exactly the production controller operation being fenced
def InstallGate(Harness: SessionHost, Operation: str) -> FilePath:
    if Operation == "claim":
        RegistryFile = Harness.RootPath / "Runners.json"
        Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
        for Field in ("group_protocol", "group_peak_memory_mib"):
            del Registry["runners"]["fixture.decode"][Field]
        _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    GateRoot = Harness.RootPath / "Gate"
    GateRoot.mkdir(mode=0o700)
    AdapterFile = GateRoot / "GateAdapter.py"
    _ = AdapterFile.write_text(
        """import json
import os
import sys
from pathlib import Path
if __name__ == "__main__":
    sys.path.insert(0, GATE_MODULE_DIRECTORY)
    from OwnerGate import GateCommand
    raise SystemExit(GateCommand(Path(__file__).resolve().parent))

from Adapters import A03Adapter

class GateAdapter(A03Adapter):
    def __init__(self, options):
        super().__init__({'store': options['store']})
        root = Path(__file__).resolve().parent / 'Processes'
        root.mkdir(mode=0o700, exist_ok=True)
        (root / f'{os.getpid()}.json').write_text(json.dumps({'pid': os.getpid(), 'parent_pid': os.getppid()}), encoding='utf-8')
        self.command = [sys.executable, __file__, str(os.getpid()), options['operation'], '--', *self.command]
""".replace("GATE_MODULE_DIRECTORY", repr(str(FilePath(__file__).resolve().parent))),
        encoding="utf-8",
    )
    Config = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    Config["controller"] = {
        "module": str(AdapterFile),
        "class": "GateAdapter",
        "options": {
            "store": str(Harness.StorePath),
            "operation": Operation,
        },
    }
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
    return GateRoot
