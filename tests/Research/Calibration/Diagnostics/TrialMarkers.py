import json as JsonCodec
from pathlib import Path as FilePath


# fixed marker names locate interrupted trials without reading private process records
def TrialMarkers(OutputPath: FilePath) -> str:
    FileNames = (
        "Prepared.json",
        "RegistryContract.json",
        "SupervisorProcess.json",
        "SupervisorInterpreter.json",
        "Cleanup.json",
        "RecoveryReceipt.json",
        "Trial.json",
    )
    Evidence: dict[str, list[str]] = {}
    for NameText in (
        "Trial1",
        "Trial2",
        "Trial4",
        "Trial8",
        "Trial16",
        "Singleton",
        "Grouped",
    ):
        TrialPath = OutputPath / NameText
        if TrialPath.is_dir():
            Evidence[TrialPath.name] = [
                FileName for FileName in FileNames if (TrialPath / FileName).is_file()
            ]
    return "\nTrial output markers: " + JsonCodec.dumps(Evidence)
