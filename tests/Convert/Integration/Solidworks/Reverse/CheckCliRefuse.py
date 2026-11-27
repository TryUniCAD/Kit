from pathlib import Path as FilePath
import subprocess as ProcessLayer
import sys as System


# unmeasured reversed parts must reach the native publication gate without replacing prior output
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
        "publication requires an offline native measurement receipt"
        in Refusal.stdout + Refusal.stderr
    )
    assert Target.read_bytes() == b"preserved"
