from pathlib import Path as FilePath

from tests.Convert.Commands.CliProcess import CliProcess


# the same receipt must refuse a different windows directory without replacing an existing output
def RefuseMeasPath(Source: FilePath, Target: FilePath, ReceiptPath: FilePath) -> None:
    Original = b"previous output"
    _ = Target.write_bytes(Original)
    Outcome = CliProcess(
        Target.parent,
        "convert",
        str(Source),
        str(Target),
        "--json",
        "--overwrite",
        "--native-measurement",
        str(ReceiptPath),
    )
    assert Outcome.returncode == 1, Outcome.stdout + Outcome.stderr
    assert "no unique exact native measurement" in Outcome.stderr
    assert Target.read_bytes() == Original
    assert set(Target.parent.iterdir()) == {Source, Target, ReceiptPath}
