import sys
from subprocess import Popen as StartProcess

if sys.platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP as KNewProcessGroup


# research children need independent process groups for targeted cancellation without interrupting the launcher
def StartResearch(
    Arguments: list[str], OwnWindows: bool = False
) -> StartProcess[bytes]:
    if sys.platform == "win32":
        if OwnWindows:
            return StartProcess(Arguments, creationflags=KNewProcessGroup)
    return StartProcess(Arguments, start_new_session=sys.platform != "win32")
