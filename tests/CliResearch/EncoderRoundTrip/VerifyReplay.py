from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath, PureWindowsPath
from subprocess import run as RunProcess
from sys import executable as PythonExec


# durable role inputs must reproduce native candidates after the original research source becomes unavailable
def VerifyReplay(
    TmpPath: FilePath,
    RootPath: FilePath,
    OutputPath: FilePath,
    SourcePath: FilePath,
) -> None:
    Snapshot = {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}
    Manifest = DecodeJson(Snapshot["manifest.json"])
    assert Manifest["schema"] == 2
    assert (
        Manifest["models_used"]
        is Manifest["vendor_loadable"]
        is Manifest["application_usable"]
        is False
    )
    assert (
        SourcePath.resolve().is_relative_to(TmpPath.resolve()) and SourcePath.is_file()
    )
    SourcePath.unlink()
    assert not SourcePath.exists()
    ReplayPath = TmpPath / "WriterReplayInputs"
    ReplayPath.mkdir()
    for RoleName in ("reconstruction", "edited"):
        Artifact = Manifest[RoleName]["writer_input"]
        assert Artifact["path"] == RoleName + "-writer-input.json"
        InputBytes = Snapshot[Artifact["path"]]
        assert len(InputBytes) == Artifact["bytes"]
        assert (
            HashContent(InputBytes).hexdigest()
            == Artifact["sha256"]
            == Manifest["writer_input_sha256"][RoleName]
        )
        InputPath = ReplayPath / Artifact["path"]
        _ = InputPath.write_bytes(InputBytes)
        ScratchPath = TmpPath / ("Replayed" + RoleName.title())
        Result = RunProcess(
            (
                PythonExec,
                "-I",
                "-B",
                str(RootPath / "re/tooling/sw2026/PreparePlainPartEvidence.py"),
                "--neutral",
                str(InputPath),
                "--native-locator",
                Manifest["native_locators"][RoleName],
                "--written-at",
                str(Manifest["written_at"]),
                "--scratch",
                str(ScratchPath),
            ),
            cwd=ReplayPath,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert Result.returncode == 0, Result.stdout + Result.stderr
        CandidateBytes = (
            ScratchPath / PureWindowsPath(Manifest["native_locators"][RoleName]).name
        ).read_bytes()
        assert CandidateBytes == Snapshot[RoleName + ".SLDPRT"]
        assert (
            HashContent(CandidateBytes).hexdigest()
            == Manifest["candidate_sha256"][RoleName]
        )
        Receipt = DecodeJson((ScratchPath / "Candidate.json").read_bytes())
        assert (Receipt["stage"], Receipt["runtime_input_reads"]) == (
            "awaiting_native_measurement",
            0,
        )
        assert InputPath.read_bytes() == InputBytes
    assert not SourcePath.exists()
    assert {
        Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()
    } == Snapshot
