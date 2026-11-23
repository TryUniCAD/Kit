from http.server import BaseHTTPRequestHandler as HttpHandler
from http.server import ThreadingHTTPServer as HttpServer
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ProcessResult
from subprocess import run as RunProcess
from sys import executable as PythonExe
from threading import Thread as WorkerThread
from urllib.parse import quote as QuotePath

from pytest import mark as MarkValue

from tests.Research.Custody.CaptureRetryWitness import (
    KFixturePath,
    KRepository,
    KRevision,
)

# immutable fixture bytes distinguish an accepted download from a mismatched response
KFixture = b'{"capture":"verified"}\n'


# a fresh git repository gives each hydration process its own object store and transport configuration
def GitFixture(Directory: FilePath) -> FilePath:
    Target = Directory / "Target"
    Remote = Directory / "Empty.git"
    _ = RunProcess(
        ("git", "init", str(Target)), check=True, capture_output=True, timeout=30
    )
    _ = RunProcess(
        ("git", "init", "--bare", str(Remote)),
        check=True,
        capture_output=True,
        timeout=30,
    )
    _ = RunProcess(
        ("git", "config", f"url.{Remote.as_uri()}.insteadOf", KRepository),
        cwd=Target,
        check=True,
        capture_output=True,
        timeout=30,
    )
    return Target


# the server receives the actual encoded request and returns the status assigned to that attempt
def RequestHandler(
    Statuses: tuple[int, ...], Content: bytes, Requests: list[str]
) -> type[HttpHandler]:

    # the standard server dispatches get requests to this method using its protocol name
    def SendFixtureMut(Handler: HttpHandler) -> None:
        Status = Statuses[len(Requests)] if len(Requests) < len(Statuses) else 500
        Requests.append(Handler.path)
        Handler.send_response(Status)
        Payload = Content if Status == 200 else b""
        Handler.send_header("Content-Length", str(len(Payload)))
        Handler.end_headers()
        _ = Handler.wfile.write(Payload)

    return type("FixtureResponse", (HttpHandler,), {"do_GET": SendFixtureMut})


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


# real http responses and git writes prove retries recover transient errors without accepting other failures
@MarkValue.parametrize(
    "Statuses,Content,ExpectedRequests,ErrorText",
    (
        ((503, 200), KFixture, 2, b""),
        ((503, 503, 503), KFixture, 3, b"download returned HTTP 503"),
        ((404,), KFixture, 1, b"download returned HTTP 404"),
        ((503, 200), b"wrong content", 2, b"failed content verification"),
    ),
)
def CheckHydration(
    TmpPath: FilePath,
    Statuses: tuple[int, ...],
    Content: bytes,
    ExpectedRequests: int,
    ErrorText: bytes,
) -> None:
    Target = GitFixture(TmpPath)
    ExpectedSha = (
        RunProcess(
            ("git", "hash-object", "--stdin"),
            cwd=Target,
            input=KFixture,
            check=True,
            capture_output=True,
            timeout=30,
        )
        .stdout.decode("ascii")
        .strip()
    )
    Reply, Requests = RunWitness(Target, ExpectedSha, Statuses, Content)
    ExpectedPath = f"/Test/Fixture/{KRevision}/{QuotePath(KFixturePath)}"
    assert Requests == [ExpectedPath] * ExpectedRequests, Reply.stderr
    if ErrorText:
        assert Reply.returncode == 1 and ErrorText in Reply.stderr
        Objects = RunProcess(
            ("git", "count-objects"),
            cwd=Target,
            capture_output=True,
            check=True,
            timeout=30,
        )
        assert Objects.stdout.startswith(b"0 objects")
    else:
        assert Reply.returncode == 0 and Reply.stdout.strip() == b"1", Reply.stderr
        Stored = RunProcess(
            ("git", "cat-file", "blob", ExpectedSha),
            cwd=Target,
            capture_output=True,
            check=True,
            timeout=30,
        )
        assert Stored.stdout == KFixture
