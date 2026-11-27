from http.server import ThreadingHTTPServer as HttpServer
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ProcessResult
from subprocess import run as RunProcess
from sys import executable as PythonExe
from threading import Thread as WorkerThread

from tests.Research.Custody.RequestHandler import RequestHandler


# the socket server stays alive until the separate hydration process has finished
def RunWitness(
    Target: FilePath, ExpectedSha: str, Statuses: tuple[int, ...], Content: bytes
) -> tuple[ProcessResult[bytes], list[str]]:
    Requests: list[str] = []
    with HttpServer(
        ("127.0.0.1", 0), RequestHandler(Statuses, Content, Requests)
    ) as Server:
        Thread = WorkerThread(target=Server.serve_forever)
        Thread.start()
        try:
            Reply = RunProcess(
                (
                    PythonExe,
                    str(FilePath(__file__).with_name("CaptureRetryWitness.py")),
                    str(Target),
                    ExpectedSha,
                    str(Server.server_port),
                ),
                capture_output=True,
                check=False,
                timeout=50,
            )
        finally:
            Server.shutdown()
            Thread.join(timeout=10)
    return Reply, Requests
