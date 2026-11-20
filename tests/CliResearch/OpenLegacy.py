from contextlib import contextmanager as Contextmanager
from collections.abc import Iterator
from pathlib import Path as FilePath
from subprocess import run as RunProcess


# linked fixtures must release repository registrations even when a reader assertion fails
@Contextmanager
def OpenLegacy(RootPath: FilePath, ParentPath: FilePath) -> Iterator[FilePath]:
    Checkout = ParentPath / "LegacyCheckout"
    Result = RunProcess(
        [
            "git",
            "-C",
            str(RootPath),
            "worktree",
            "add",
            "--detach",
            str(Checkout),
            "520f0f5a9a96d3bcc0364c97b1add413ccac86ab",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    try:
        yield Checkout
    finally:
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
