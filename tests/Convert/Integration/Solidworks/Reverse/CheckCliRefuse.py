from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System


# incomplete source semantics must refuse conversion before replacing an existing destination
def CheckCliRefuse(
    Source: FilePath, Target: FilePath, RootPath: FilePath, Environment: dict[str, str]
) -> None:
    _ = Target.write_bytes(b"preserved")
    Refusal = ProcessLayer.run(
        [
            System.executable,
            "-m",
            "KitCli",
            "convert",
            str(Source),
            str(Target),
            "--overwrite",
        ],
        cwd=RootPath,
        env=Environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Refusal.returncode != 0
    assert (
        "NativeFeature records are not conversion-ready"
        in Refusal.stdout + Refusal.stderr
    )
    assert Target.read_bytes() == b"preserved"
