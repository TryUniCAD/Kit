from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook


# a real competing filesystem entry must reach the native link call after comparison succeeds
def ObstructCopy(EventName: str, Arguments: tuple[object, ...]) -> None:
    if EventName != "os.link" or len(Arguments) < 2:
        return
    Destination = Arguments[1]
    Target = FilePath.cwd() / "Output" / "unified" / "0000.json"
    if isinstance(Destination, (str, FilePath)) and FilePath(Destination) == Target:
        Target.mkdir()


AddAuditHook(ObstructCopy)
