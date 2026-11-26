from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.Research.Inference.Authoring.Pipeline.ReadAccepted import ReadAccepted
from tests.Research.Inference.Authoring.Pipeline.RunSupervisor import RunSupervisor
from tests.Research.Inference.Authoring.Recipes.PrepareBatch import PrepareBatch
from tests.Research.Inference.Authoring.Recipes.ReadBatchState import ReadBatchState


# a refused first member must leave the later sibling able to decode its original bundle role
def CheckRejection(TmpPath: FilePath) -> None:
    StorePath, ConfigPath = PrepareBatch(TmpPath, "native-rejected")
    Summary = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    JobRows = {Entry["id"]: Entry for Entry in Summary["jobs"]}
    assert JobRows["fixture-native"]["state"] == "completed"
    assert JobRows["decode-first"]["state"] == "waiting_evidence"
    assert JobRows["decode-first"]["attempts"] == 0
    Sibling = JobRows["decode-second"]
    assert Sibling["state"] == "completed"
    Receipt = DecodeJson(ReadAccepted(StorePath, Sibling["result"]))
    Files = [Sample["file"] for Sample in Receipt["result"]["records"]["samples"]]
    assert Files == ["Second.f3d"]
    Outcome = ReadBatchState(TmpPath)
    assert Outcome["status"] == "failed"
    assert Outcome["native_verified_samples"] == 0
    assert Outcome["samples"]["fusion:second"]["status"] == "decode_unresolved"
    Rejected = Outcome["samples"]["fusion:first"]
    assert Rejected["status"] == "failed"
    assert Rejected["native_rejection"] == "fixture measurement mismatch"
