from contextlib import contextmanager as Contextmanager
from collections.abc import Iterator
from pathlib import Path as FilePath
from subprocess import run as RunProcess

# reader compatibility must remain bound to the verified preverification checkout
KLegacyRevision = "520f0f5a9a96d3bcc0364c97b1add413ccac86ab"


# linked fixtures must release repository registrations even when a reader assertion fails
@Contextmanager
def OpenLegacy(
    RootPath: FilePath, ParentPath: FilePath, Revision: str = KLegacyRevision
) -> Iterator[FilePath]:
    Checkout = ParentPath / "LegacyCheckout"
    try:
        Result = RunProcess(
            [
                "git",
                "-C",
                str(RootPath),
                "worktree",
                "add",
                "--detach",
                "--no-checkout",
                str(Checkout),
                Revision,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert Result.returncode == 0, Result.stderr
        for GitArgs in (
            ("sparse-checkout", "set", "--cone", "src", "re/automation"),
            ("read-tree", "-mu", "HEAD"),
        ):
            GitResult = RunProcess(
                ("git", "-C", str(Checkout), *GitArgs),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            assert GitResult.returncode == 0, GitResult.stderr
        yield Checkout
    finally:
        if (Checkout / ".git").exists():
            Removed = RunProcess(
                [
                    "git",
                    "-C",
                    str(RootPath),
                    "worktree",
                    "remove",
                    "--force",
                    str(Checkout),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            assert Removed.returncode == 0, Removed.stderr
