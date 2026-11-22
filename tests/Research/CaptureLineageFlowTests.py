from json import dumps as EncodeJson, loads as ParseJson
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from tempfile import TemporaryDirectory as MakeFolder

from pytest import mark as MarkValue

# fixture mutations affect only their private index and detached object store
KSpecPath = "re/automation/PairSpecs.json"

# each approved text migration must still reject arbitrary content mode and roster changes
KMigrationPaths = (
    "re/automation/Corpus.json",
    "re/automation/PairedCaptures/SolidWorksAuthoring/BossWitnessReadback.cs",
    "re/automation/PairedCaptures/SolidWorksAuthoring/P02Readback.cs",
    "re/automation/PairedCaptures/SolidWorksAuthoring/RunBossWitness.ps1",
)


# real git commands keep the fixture at the repository boundary with bounded output
def RunGit(
    RootPath: FilePath,
    *Arguments: str,
    InputData: bytes | None = None,
    IndexPath: FilePath | None = None,
) -> bytes:
    Environment = {
        **{
            EnvName: Value
            for EnvName, Value in ProcessEnv.items()
            if not EnvName.startswith("GIT_")
        },
        "GIT_AUTHOR_NAME": "Lineage fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Lineage fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        "GIT_NO_LAZY_FETCH": "1",
    }
    if IndexPath is not None:
        Environment["GIT_INDEX_FILE"] = str(IndexPath)
    Result = RunProcess(
        ["git", "-C", str(RootPath), *Arguments],
        input=InputData,
        capture_output=True,
        env=Environment,
        check=False,
        timeout=120,
    )
    assert Result.returncode == 0, Result.stderr.decode("utf-8", "replace")
    assert len(Result.stdout) <= 32 * 1024 * 1024
    return Result.stdout


# a detached bare fixture reads existing objects without creating or updating any branch
def MakeBare(RootPath: FilePath, Directory: FilePath, Revision: str) -> FilePath:
    BarePath = Directory / "Metadata.git"
    (BarePath / "objects" / "info").mkdir(parents=True)
    (BarePath / "refs").mkdir()
    _ = (BarePath / "HEAD").write_text(Revision + "\n", encoding="ascii")
    _ = (BarePath / "config").write_text(
        "[core]\nrepositoryformatversion = 0\nbare = true\n", encoding="ascii"
    )
    CommonPath = FilePath(
        RunGit(RootPath, "rev-parse", "--path-format=absolute", "--git-common-dir")
        .decode("utf-8")
        .strip()
    )
    _ = (BarePath / "objects" / "info" / "alternates").write_text(
        (CommonPath / "objects").as_posix() + "\n", encoding="utf-8"
    )
    assert RunGit(BarePath, "rev-parse", "--is-bare-repository").strip() == b"true"
    return BarePath


# source mutations retain valid git structure while changing only declared capture inputs
def MutateIndex(
    BarePath: FilePath, IndexPath: FilePath, Revision: str, CaseMode: str
) -> None:
    if CaseMode.startswith("attribution-"):
        Mutation, TargetPath = CaseMode.split(":", 1)
        if Mutation == "attribution-missing":
            _ = RunGit(
                BarePath,
                "update-index",
                "--index-info",
                InputData=f"0 {'0' * 40}\t{TargetPath}\n".encode(),
                IndexPath=IndexPath,
            )
            return
        BlobValue = RunGit(BarePath, "rev-parse", f"{Revision}:{TargetPath}")
        if Mutation == "attribution-content":
            SourceBytes = RunGit(BarePath, "show", f"{Revision}:{TargetPath}")
            BlobValue = RunGit(
                BarePath,
                "hash-object",
                "-w",
                "--stdin",
                InputData=SourceBytes + b"\nunapproved attribution edit\n",
            )
        _ = RunGit(
            BarePath,
            "update-index",
            "--cacheinfo",
            f"{'100755' if Mutation == 'attribution-mode' else '100644'},{BlobValue.decode().strip()},{TargetPath}",
            IndexPath=IndexPath,
        )
        return
    if CaseMode == "changed-spec":
        BlobValue = RunGit(BarePath, "hash-object", "-w", "--stdin", InputData=b"{}\n")
        _ = RunGit(
            BarePath,
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{BlobValue.decode().strip()},{KSpecPath}",
            IndexPath=IndexPath,
        )
    elif CaseMode == "extra-input":
        BlobValue = RunGit(
            BarePath, "hash-object", "-w", "--stdin", InputData=b"unbound\n"
        )
        _ = RunGit(
            BarePath,
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{BlobValue.decode().strip()},re/automation/PairedCaptures/Unbound.txt",
            IndexPath=IndexPath,
        )
    elif CaseMode == "outside-alias":
        TreeValue = RunGit(
            BarePath, "ls-tree", "-rz", Revision, "--", "re/automation/PairedCaptures/"
        )
        AliasBlob = next(
            EntryRow.split(b"\t", 1)[0].split()[2].decode("ascii")
            for EntryRow in TreeValue.split(b"\0")
            if EntryRow and EntryRow.lower().endswith(b".f3d")
        )
        _ = RunGit(
            BarePath,
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{AliasBlob},re/Other/Alias.f3d",
            IndexPath=IndexPath,
        )
    elif CaseMode == "mode-change":
        BlobValue = RunGit(BarePath, "rev-parse", f"{Revision}:{KSpecPath}")
        _ = RunGit(
            BarePath,
            "update-index",
            "--cacheinfo",
            f"100755,{BlobValue.decode().strip()},{KSpecPath}",
            IndexPath=IndexPath,
        )
    elif CaseMode == "missing-input":
        _ = RunGit(
            BarePath,
            "update-index",
            "--index-info",
            InputData=f"0 {'0' * 40}\t{KSpecPath}\n".encode(),
            IndexPath=IndexPath,
        )


# temporary commits preserve the caller history and never update a named git reference
def NewRevision(
    BarePath: FilePath, Directory: FilePath, Revision: str, CaseMode: str
) -> str:
    IndexPath = Directory / "Input.index"
    _ = RunGit(BarePath, "read-tree", Revision, IndexPath=IndexPath)
    MutateIndex(BarePath, IndexPath, Revision, CaseMode)
    TreeValue = RunGit(BarePath, "write-tree", IndexPath=IndexPath).decode().strip()
    return (
        RunGit(
            BarePath,
            "commit-tree",
            TreeValue,
            "-p",
            Revision,
            InputData=b"lineage fixture\n",
        )
        .decode()
        .strip()
    )


# exact input binding cannot turn historical capture gaps into native qualification
def AssertLineage(ResultData: dict[str, object], Revision: str) -> None:
    Report = ParseJson(EncodeJson(ResultData))
    assert Report["source_revision"] == Revision
    assert (
        Report["historical_lineage"]["lineage_revision"]
        == "f5b23031c4163528a2e4f5029ab34102133b983e"
    )
    assert (
        Report["historical_lineage"]["input_tree_sha256"]
        == "ca44feca3f2ca32cd852f32e4afde2e5a2b334a8c83a150e813d8256f6c106b6"
    )
    assert Report["historical_lineage"]["bound_input_count"] == 130
    assert (
        Report["historical_lineage"]["binding"]
        == "pinned_attribution_and_identical_tracked_file_modes_and_blob_ids"
    )
    assert len(Report["historical_lineage"]["current_input_tree_sha256"]) == 64
    assert {
        Entry["path"]
        for Entry in Report["historical_lineage"]["attribution_migrations"]
    } == set(KMigrationPaths)
    assert Report["summary"]["capture_receipts"] == 10
    assert Report["summary"]["native_files"] == 74
    assert Report["summary"]["qualified_pairs"] == 0
    assert all(
        Capture["introduction_revision"] != Revision for Capture in Report["captures"]
    )


# override fixtures stay private while preserving the same public lineage contract
def BindOverrideMut(
    BarePath: FilePath, Current: str, Contract: dict[str, str], CaseMode: str
) -> None:
    if CaseMode == "replaced-source":
        _ = RunGit(
            BarePath,
            "update-ref",
            "refs/replace/" + Contract["source_revision"],
            Current,
        )
    if CaseMode == "grafted-source":
        (BarePath / "info").mkdir()
        _ = (BarePath / "info" / "grafts").write_text(
            Contract["source_revision"] + " " + Current + "\n", encoding="ascii"
        )
    if CaseMode == "shallow-source":
        _ = (BarePath / "shallow").write_text(
            Contract["source_revision"] + "\n", encoding="ascii"
        )
    if CaseMode == "contract-mismatch":
        Contract["input_tree_sha256"] = "0" * 64
    if CaseMode == "missing-lineage":
        Contract["source_revision"] = "0" * 40


# public intake distinguishes original provenance from current bytes across actual git mutations
@MarkValue.parametrize(
    "CaseMode",
    (
        "intact",
        "changed-spec",
        "extra-input",
        "mode-change",
        "missing-input",
        "replaced-source",
        "grafted-source",
        "contract-mismatch",
        "missing-lineage",
        "outside-alias",
        "shallow-source",
        *(
            f"{Mutation}:{PathValue}"
            for Mutation in (
                "attribution-content",
                "attribution-mode",
                "attribution-missing",
            )
            for PathValue in KMigrationPaths
        ),
    ),
)
def CheckLineage(CaseMode: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Revision = RunGit(RootPath, "rev-parse", "HEAD").decode().strip()
    Contract = ParseJson((RootPath / "re/automation/CaptureLineage.json").read_bytes())
    with MakeFolder() as TempRoot:
        Directory = FilePath(TempRoot)
        BarePath = MakeBare(RootPath, Directory, Revision)
        Current = NewRevision(BarePath, Directory, Revision, CaseMode)
        BindOverrideMut(BarePath, Current, Contract, CaseMode)
        ContractPath = Directory / "Lineage.json"
        _ = ContractPath.write_text(EncodeJson(Contract), encoding="utf-8")
        Result = RunProcess(
            [
                PythonExe,
                str(RootPath / "re/automation/PairedCaptureIntake.py"),
                "--root",
                str(BarePath),
                "--revision",
                Current,
                "--lineage-contract",
                str(ContractPath),
            ],
            capture_output=True,
            check=False,
            timeout=180,
        )
        assert RunGit(BarePath, "for-each-ref", "refs/heads/") == b""
        if CaseMode in {"intact", "replaced-source", "grafted-source"}:
            assert Result.returncode == 0, Result.stderr.decode("utf-8", "replace")
            AssertLineage(ParseJson(Result.stdout), Current)
        elif CaseMode == "outside-alias":
            assert Result.returncode == 2, Result.stderr.decode("utf-8", "replace")
            Report = ParseJson(Result.stdout)
            AssertLineage(Report, Current)
            assert Report["quarantined_families"]
            assert any(
                "re/Other/Alias.f3d" in NativeItem["git_tree_aliases"]
                for Capture in Report["captures"]
                for NativeItem in Capture["native_files"]
            )
            assert all(
                "native_blob_alias_or_reuse" in Capture["qualification_blockers"]
                and Capture["permitted_use"] == "quarantine"
                for Capture in Report["captures"]
                if Capture["family"] in Report["quarantined_families"]
            )
        else:
            assert Result.returncode == 1 and not Result.stdout
            assert b"paired capture intake failed:" in Result.stderr


# the public snapshot command must read original blobs through its streaming git process
@MarkValue.parametrize("CaseMode", ("plain", "replaced-blob", "hostile-git"))
def CheckSnapshot(CaseMode: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Revision = RunGit(RootPath, "rev-parse", "HEAD").decode().strip()
    with MakeFolder() as TempRoot:
        Directory = FilePath(TempRoot)
        BarePath = MakeBare(RootPath, Directory, Revision)
        Original = b"authored corpus identity fixture\n"
        BlobValue = (
            RunGit(BarePath, "hash-object", "-w", "--stdin", InputData=Original)
            .decode()
            .strip()
        )
        IndexPath = Directory / "Snapshot.index"
        _ = RunGit(BarePath, "read-tree", "--empty", IndexPath=IndexPath)
        _ = RunGit(
            BarePath,
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{BlobValue},re/Fusion/examples/Identity.f3d",
            IndexPath=IndexPath,
        )
        TreeValue = RunGit(BarePath, "write-tree", IndexPath=IndexPath).decode().strip()
        Current = (
            RunGit(BarePath, "commit-tree", TreeValue, InputData=b"snapshot fixture\n")
            .decode()
            .strip()
        )
        if CaseMode == "replaced-blob":
            Other = RunGit(
                BarePath, "hash-object", "-w", "--stdin", InputData=b"altered\n"
            )
            _ = RunGit(
                BarePath,
                "update-ref",
                "refs/replace/" + BlobValue,
                Other.decode().strip(),
            )
        VerifySnapshot(
            RootPath, BarePath, Directory, Current, BlobValue, Original, CaseMode
        )
        assert RunGit(BarePath, "for-each-ref", "refs/heads/") == b""


# hostile git overrides are limited to the child under test and cannot redirect fixture writes
def VerifySnapshot(
    RootPath: FilePath,
    BarePath: FilePath,
    Directory: FilePath,
    Revision: str,
    BlobValue: str,
    Original: bytes,
    CaseMode: str,
) -> None:
    OutputPath = Directory / "Snapshot.json"
    Environment = dict(ProcessEnv)
    if CaseMode == "hostile-git":
        Environment["GIT_DIR"] = str(Directory / "Missing.git")
        Environment["GIT_OBJECT_DIRECTORY"] = str(Directory / "MissingObjects")
    Result = RunProcess(
        [
            PythonExe,
            str(RootPath / "re/automation/Corpus.py"),
            "snapshot",
            "--root",
            str(BarePath),
            "--revision",
            Revision,
            "--manifest",
            str(OutputPath),
        ],
        capture_output=True,
        check=False,
        timeout=180,
        env=Environment,
    )
    assert Result.returncode == 0, Result.stderr.decode("utf-8", "replace")
    Report = ParseJson(OutputPath.read_bytes())
    assert len(Report["assets"]) == 1
    assert Report["assets"][0]["git_blob"] == BlobValue
    assert Report["assets"][0]["prefix_hex"] == Original[:16].hex()
    assert Report["assets"][0]["size_bytes"] == len(Original)
    assert Report["summary"]["native_acceptance"] == "not_established"
