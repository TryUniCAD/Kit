from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from struct import pack as PackValue
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

from pytest import mark as MarkValue

from tests.Research.Inference.InferenceSession import WriteSession

# real standalone commands must consume the same checkout and source identity as the candidate
KRepoRoot = FilePath(__file__).resolve().parents[3]

# the through all assessment needs accepted process evidence before it can claim a grid
KGridScope = "p04-through-all-body-selection"


# actual content addressed session files exercise the runner input pin boundary
def WriteInput(RootPath: FilePath, RoleName: str, Content: bytes) -> dict[str, str]:
    Inputs = RootPath / "inputs"
    Inputs.mkdir(exist_ok=True)
    PinValue = DigestBytes(Content).hexdigest()
    assert (Inputs / PinValue).write_bytes(Content) == len(Content)
    return {"binding": RoleName, "sha256": PinValue, "path": f"inputs/{PinValue}"}


# independently authored protocol reports make no application or native geometry claim
def GapReport(ScopeName: str, Status: str) -> dict[str, object]:
    return {
        "inference_version": 1,
        "scope": ScopeName,
        "status": Status,
        "affected_archives": {
            DigestBytes(b"authored fusion identity").hexdigest(): "fusion.f3d",
            DigestBytes(
                b"authored solidworks identity"
            ).hexdigest(): "solidworks.sldprt",
        },
        "requested_grid": {"fixture": "independent distinguishing input needed"},
        "corroboration": {"fixture": "authored generic protocol evidence"},
        "counterexamples": {"fixture": "authored generic protocol counterexample"},
    }


# process completion and durable result publication remain separately observable
def InvokeWorker(RootPath: FilePath) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/InferenceRunner.py"),
            str(RootPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


# every generic inference outcome retains explicit unqualified receipts
def AssertReceipt(
    RootPath: FilePath, Process: CompletedProcess[str]
) -> dict[str, object]:
    assert Process.returncode == 0, Process.stderr
    Result = CastValue(
        dict[str, object],
        ParseJson((RootPath / "result.json").read_text(encoding="utf-8")),
    )
    Records = CastValue(dict[str, object], Result["records"])
    assert Records["semantic_qualification"] == "unverified"
    assert (
        Records["native_acceptance"] == "not_established"
        and Records["portable_complete"] is False
    )
    Packet = ParseJson((RootPath / "job.json").read_bytes())
    Execution = CastValue(dict[str, object], Records["execution"])
    assert Execution["fingerprint"] == Packet["fingerprint"]
    assert (
        Execution["definition_sha256"]
        == DigestBytes(
            EncodeJson(
                Packet["job"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()
    )
    assert Execution["rule_version"] == Packet["job"]["rule_version"]
    assert Execution["tool_version"] == Packet["job"]["tool_version"]
    assert Execution["input_sha256"] == {
        RoleName: Descriptor["sha256"]
        for RoleName, Descriptor in Packet["inputs"].items()
    }
    return Result


# generic parked corroborated and refuted reports must work without loading excluded native proof modules
@MarkValue.parametrize(
    "Status", ("needs-distinguishing-evidence", "corroborated", "refuted")
)
def CheckGap(TmpPath: FilePath, Status: str) -> None:
    Scope = "authored-generic-gap"
    Payload = EncodeJson(GapReport(Scope, Status), sort_keys=True).encode()
    Descriptor = WriteInput(TmpPath, "plan", Payload)
    WriteSession(TmpPath, "inference.paired-gap", Scope, {"plan": Descriptor})
    Result = AssertReceipt(TmpPath, InvokeWorker(TmpPath))
    assert Result["outcome"] == (
        "waiting_evidence" if Status == "needs-distinguishing-evidence" else "completed"
    )
    Records = CastValue(dict[str, object], Result["records"])
    assert Records["report_sha256"] == Descriptor["sha256"]
    assert CastValue(dict[str, object], Records["assessment"])["status"] == Status
    assert (TmpPath / Descriptor["path"]).read_bytes() == Payload


# untrusted reports cannot substitute claims for an authenticated native grid
@MarkValue.parametrize(
    "CaseName",
    ("corroborated-grid", "native_grid", "continued_from_receipt", "grid_from_receipt"),
)
def CheckReserved(TmpPath: FilePath, CaseName: str) -> None:
    Scope = KGridScope if CaseName == "corroborated-grid" else "authored-generic-gap"
    Report = GapReport(Scope, "corroborated")
    if CaseName in ("native_grid", "continued_from_receipt"):
        Report[CaseName] = {"fixture": "must not substitute for native proof"}
    Payload = EncodeJson(Report).encode()
    Descriptor = WriteInput(TmpPath, "plan", Payload)
    Extra = {"grid_from_receipt": "0" * 64} if CaseName == "grid_from_receipt" else None
    WriteSession(TmpPath, "inference.paired-gap", Scope, {"plan": Descriptor}, Extra)
    Process = InvokeWorker(TmpPath)
    assert Process.returncode == 1 and "inference refused:" in Process.stderr
    assert "authenticated" in Process.stderr or "assessment mode" in Process.stderr
    assert not (TmpPath / "result.json").exists()
    assert (TmpPath / Descriptor["path"]).read_bytes() == Payload


# scheduling must pin the dependent rescan to the field search it uses
@MarkValue.parametrize("Scope", ("authored-generic-fields", "p03-blind-boss.fusion"))
def CheckSchedule(TmpPath: FilePath, Scope: str) -> None:
    Request: dict[str, object] = {
        "inference_version": 1,
        "scope": Scope,
        "family": "authored",
        "rule_version": "fixture@1",
        "tool_version": "main-sdk-boundary@1",
        "plan_input": "plan",
        "stream_inputs": {"sample": "stream"},
        "archives": {
            DigestBytes(b"source").hexdigest(): {
                "binding": "source",
                "format": "solidworks.sldprt",
            }
        },
        "distinguishing_evidence": [],
        "depends_on": [],
    }
    RequestFile = TmpPath / "Request.json"
    Before = EncodeJson(Request)
    _ = RequestFile.write_text(Before, encoding="utf-8")
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/InferenceSchedule.py"),
            str(RequestFile),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr
    JobRows = ParseJson(Process.stdout)["jobs"]
    assert [JobValue["kind"] for JobValue in JobRows] == [
        "inference.fields",
        "inference.rescan",
    ]
    assert JobRows[1]["depends_on"] == [JobRows[0]["id"]]
    assert all(
        JobValue["tool_version"] == "main-sdk-boundary@1" for JobValue in JobRows
    )
    assert RequestFile.read_text(encoding="utf-8") == Before


# authored binary streams distinguish the generic numeric search from any native format grammar
def WriteFieldPlan(RootPath: FilePath, Refute: bool) -> dict[str, dict[str, str]]:
    Samples: list[dict[str, object]] = []
    Provenance: dict[str, dict[str, str]] = {}
    Inputs: dict[str, dict[str, str]] = {}
    for Index, (Value, Split) in enumerate(
        ((1.25, "discovery"), (2.75, "discovery"), (4.5, "holdout"))
    ):
        Identity = f"sample-{Index}"
        Content = PackValue("<d", 6.25 if Refute and Split == "holdout" else Value)
        Descriptor = WriteInput(RootPath, Identity, Content)
        Inputs[Identity] = Descriptor
        Provenance[Identity] = {
            "archive_sha256": Descriptor["sha256"],
            "stream_sha256": Descriptor["sha256"],
        }
        Samples.append(
            {
                "id": Identity,
                "lineage": (
                    "independently-authored"
                    if Split == "holdout"
                    else "authored-discovery"
                ),
                "sha256": Descriptor["sha256"],
                "stream": "authored.numeric",
                "start": 0,
                "length": 8,
                "value": Value,
                "controls": {},
                "role": Identity,
                "split": Split,
            }
        )
    PlanValue: dict[str, object] = {
        "inference_version": 1,
        "scope": "authored-generic-fields",
        "quantity": "authored-scalar",
        "provenance": {"inputs": Provenance},
        "encodings": [
            {
                "type": "f64",
                "endian": "little",
                "unit": "authored-unit",
                "scale": 1,
                "offset": 0,
            }
        ],
        "tolerance": 0,
        "confounds": [],
        "observations": Samples,
    }
    Inputs["plan"] = WriteInput(RootPath, "plan", EncodeJson(PlanValue).encode())
    return Inputs


# actual field inference freezes candidates then allows an independent fixture to refute them
@MarkValue.parametrize("Refute", (False, True))
def CheckFields(TmpPath: FilePath, Refute: bool) -> None:
    Inputs = WriteFieldPlan(TmpPath, Refute)
    WriteSession(TmpPath, "inference.fields", "authored-generic-fields", Inputs)
    Result = AssertReceipt(TmpPath, InvokeWorker(TmpPath))
    Records = CastValue(dict[str, object], Result["records"])
    Assessment = CastValue(dict[str, object], Records["assessment"])
    assert Assessment["status"] == ("refuted" if Refute else "hypothesis")
    Hypotheses = CastValue(list[dict[str, object]], Assessment["hypotheses"])
    assert len(Hypotheses) == 1 and Hypotheses[0]["relative_offset"] == 0
    assert Hypotheses[0]["confidence"] == ("refuted" if Refute else "partial")
    assert Records["plan_sha256"] == Inputs["plan"]["sha256"]


# the rescan fixture uses the unchanged main control through its real git content boundary
def WriteRescan(RootPath: FilePath, Tamper: bool) -> tuple[bytes, dict[str, str]]:
    Process = RunProcess(
        [
            "git",
            "show",
            "1d294381340a36ce8e4d9e288e73d995da12fcd7:re/solidworks/examples/.SLDPRT/example.SLDPRT",
        ],
        cwd=KRepoRoot,
        capture_output=True,
        check=True,
        timeout=30,
    )
    Content = Process.stdout
    Source = WriteInput(RootPath, "source", Content)
    Scope = "authored-generic-rescan"
    Assessment = {
        "inference_version": 1,
        "kind": "inference.fields",
        "scope": Scope,
        "source_sha256": [Source["sha256"]],
    }
    Completed = {
        "session_version": 1,
        "result": {"outcome": "completed", "records": Assessment},
    }
    PlanValue = WriteInput(RootPath, "assessment", EncodeJson(Completed).encode())
    WriteSession(
        RootPath,
        "inference.rescan",
        Scope,
        {"assessment": PlanValue, "source": Source},
        {"source_format": "solidworks.sldprt", "source_sha256": Source["sha256"]},
    )
    if Tamper:
        assert (RootPath / Source["path"]).write_bytes(b"changed source") == 14
    return Content, Source


# main sdk observations retain source pins and explicit unresolved status without format expansion
@MarkValue.parametrize("Tamper", (False, True))
def CheckRescan(TmpPath: FilePath, Tamper: bool) -> None:
    Content, Source = WriteRescan(TmpPath, Tamper)
    Process = InvokeWorker(TmpPath)
    if Tamper:
        assert Process.returncode == 1 and "differed from its pin" in Process.stderr
        assert not (TmpPath / "result.json").exists()
        assert (TmpPath / Source["path"]).read_bytes() == b"changed source"
        return
    Result = AssertReceipt(TmpPath, Process)
    Records = CastValue(dict[str, object], Result["records"])
    assert Records["source_sha256"] == Source["sha256"]
    assert Records["kind"] == "inference.rescan" and Records["unresolved"]
    assert (TmpPath / Source["path"]).read_bytes() == Content
