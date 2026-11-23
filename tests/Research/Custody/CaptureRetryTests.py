from pathlib import Path as FilePath
from subprocess import run as RunProcess
from urllib.parse import quote as QuotePath

from pytest import mark as MarkValue

from tests.Research.Custody.CaptureRetryWitness import (
    KFixturePath,
    KRevision,
)
from tests.Research.Custody.GitFixture import GitFixture
from tests.Research.Custody.RunWitness import RunWitness

# immutable fixture bytes distinguish an accepted download from a mismatched response
KFixture = b'{"capture":"verified"}\n'


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
