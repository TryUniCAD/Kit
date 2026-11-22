from dataclasses import replace as ReplaceValue
from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson
from os import name as KOsName
from pathlib import Path as FilePath, PureWindowsPath

from convert import write_document as WriteDocument
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KAsmFormatId,
    KAsmSuffix,
    KPartSuffix,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from interchange.assembly.MateGroup import MateGroup
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.NestedWriting.MakeNestDoc import MakeNestDoc


# the authored in memory archive must retain shared nested definitions without a publication receipt
def TestNestedShape() -> None:
    DocumentValue = MakeNestDoc()
    RootName = "QueueFrame" + KAsmSuffix.upper()
    Locator = str(PureWindowsPath(r"C:\KitNestedQueue", RootName))
    Candidates = PrepNestedAsm(DocumentValue, Locator, 1794011937)
    assert tuple(PathValue.name for PathValue, _ in Candidates) == (
        "QueuePlate" + KPartSuffix.upper(),
        "QueueModule" + KAsmSuffix.upper(),
        RootName,
    )
    VerifyNestRead(Candidates[-1][1].BytesValue)


# exact native evidence is required independently of the sdk carrier preference
def TestNestStrict(TmpPath: FilePath) -> None:
    DocumentValue = MakeNestDoc()
    TargetPath = TmpPath / "strict" / "QueueFrame.SLDASM"
    for AllowCarrier in (False, True):
        try:
            _ = WriteDocument(
                DocumentValue,
                TargetPath,
                allow_carrier=AllowCarrier,
                values={
                    "native_destination": r"C:\KitNestedQueue\QueueFrame.SLDASM",
                    "require_native_transfers": True,
                },
            )
        except ValueError as Failure:
            assert "requires an offline native measurement receipt" in str(Failure)
        else:
            raise AssertionError("the registry published an unmeasured assembly")
        assert not TargetPath.parent.exists()
    if KOsName == "nt":
        return
    FixtureValue = LoadJson(
        FilePath(__file__)
        .with_name("MeasuredDimensionedBundle.json")
        .read_text(encoding="utf-8")
    )
    Source = TmpPath / "Neutral.json"
    Receipt = TmpPath / "Measurement.json"
    _ = Source.write_text(DumpJson(FixtureValue["neutral"]), encoding="utf-8")
    _ = Receipt.write_text(DumpJson(FixtureValue["measurement"]), encoding="utf-8")
    NativePath = PureWindowsPath(FixtureValue["native_destination"])
    Target = TmpPath / NativePath.name
    CommandArgs = (
        "convert",
        str(Source),
        str(Target),
        "--json",
        "--native-measurement",
        str(Receipt),
        "--native-destination",
    )
    Wrong = CliProcess(
        TmpPath, *CommandArgs, str(NativePath.parent / "Other" / NativePath.name)
    )
    assert (
        Wrong.returncode == 1
        and not Wrong.stdout
        and "namespace" in LoadJson(Wrong.stderr)["message"]
        and set(TmpPath.iterdir()) == {Source, Receipt}
    )
    Result = CliProcess(TmpPath, *CommandArgs, str(NativePath))
    assert Result.returncode == 0 and not Result.stderr, Result.stderr
    Report = LoadJson(Result.stdout)
    assert Report["application_usable"] is Report["vendor_loadable"] is True
    assert Report["dropped"] == []
    assert {
        Member.name: CalcSha(Member.read_bytes()).hexdigest()
        for Member in set(TmpPath.iterdir()) - {Source, Receipt}
    } == {
        MemberRow["name"]: MemberRow["sha256"]
        for MemberRow in FixtureValue["measurement"]["receipt"]["members"]
    }


# the native component index must resolve both root placements to one child definition and one actual part
def VerifyNestRead(Payload: bytes) -> None:
    Assembly = DecodeNativeAsm(SldprtArchive.from_bytes(Payload))
    Definitions = {
        PureWindowsPath(Value.source_path).stem: Value for Value in Assembly.definitions
    }
    assert set(Definitions) == {"QueueFrame", "QueueModule", "QueuePlate"}
    ModuleValue = Definitions["QueueModule"]
    RootRows = tuple(
        Value
        for Value in Assembly.occurrences
        if Value.owner_definition_id == Assembly.root_definition_id
    )
    assert tuple(Value.definition_id for Value in RootRows) == (
        ModuleValue.object_id,
        ModuleValue.object_id,
    )
    assert RootRows[0].transform != RootRows[1].transform
    PlateRows = tuple(
        Value
        for Value in Assembly.occurrences
        if Value.owner_definition_id == ModuleValue.object_id
    )
    assert tuple(Value.definition_id for Value in PlateRows) == (
        Definitions["QueuePlate"].object_id,
    )


# mate group content is outside the qualified rigid hierarchy and must be refused before publication
def TestNestNoMates(TmpPath: FilePath) -> None:
    DocumentValue = MakeNestDoc()
    Assembly = DocumentValue.assembly
    assert Assembly is not None
    GroupValue = MateGroup(
        "group/example", "Unrepresented", Assembly.root_definition_id, ()
    )
    Changed = ReplaceValue(
        DocumentValue, assembly=ReplaceValue(Assembly, mate_groups=(GroupValue,))
    )
    TargetPath = TmpPath / "unclaimed" / ("QueueFrame" + KAsmSuffix.upper())
    try:
        _ = WriteDocument(
            Changed,
            TargetPath,
            destination_format=KAsmFormatId,
            allow_carrier=True,
            values={"require_native_transfers": True},
        )
    except NotFoundError:
        assert not TargetPath.parent.exists()
    else:
        raise AssertionError("unsupported mate group was published")
