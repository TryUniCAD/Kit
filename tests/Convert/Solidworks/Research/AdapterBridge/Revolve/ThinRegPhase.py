from dataclasses import replace as ReplaceValue
from io import BytesIO
from math import isclose as IsClose
from pathlib import Path as FilePath
from sys import argv as Arguments, path as ImportPath
from typing import cast as CastValue
from unittest.mock import patch as PatchValue

# the fresh interpreter must resolve the exact checkout before importing the sdk
KRepoRoot = FilePath(Arguments[1])

# isolated startup needs the explicit package and test fixture roots
ImportPath[:0] = [str(KRepoRoot / "src"), str(KRepoRoot)]

from convert import open_document as OpenDoc, write_document as WriteDoc
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Container.Format import KPartFormatId, KPartSuffix
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Revolves.ThinRevolve import ThinRevolve
from tests.Convert.Solidworks.Research.AdapterBridge.Revolve.MakeThinCase import (
    MakeThinCase,
)


# the readback must retain the actual ordered angle and independent wall parameter owners
def CheckDrivers(Document: CadDocument) -> str:
    (Feature,) = (
        Value
        for Value in Document.feature_timeline
        if isinstance(Value.definition, ThinRevolve)
    )
    Definition = Feature.definition
    assert isinstance(Definition, ThinRevolve) and Definition.WallMode == "two_sided"
    Scope = (Definition.SweepValue.AlongParameterId, *Definition.GetWallIds())
    assert Feature.parameter_ids == Scope
    Parameters = {Value.id: Value for Value in Document.parameters}
    for Identity, (NameValue, UnitValue, ScalarValue) in zip(
        Scope, (("D1", "rad", 1.25), ("D3", "mm", 2.75), ("D4", "mm", 5.5)), strict=True
    ):
        Driver = Parameters[Identity]
        assert Driver.owner_id == Feature.id and Driver.name == NameValue
        assert Driver.value.unit == UnitValue
        assert IsClose(CastValue(float, Driver.value.value), ScalarValue, rel_tol=1e-12)
    return Feature.id


# the cold analytic solid must keep its actual thin feature and independently expected volume
def CheckSolid(SourceValue: FilePath | bytes, FeatureName: str) -> None:
    Document = OpenDoc(SourceValue, source_format=KPartFormatId, strict=True)
    Document.assert_valid()
    FeatureId = CheckDrivers(Document)
    (BodyValue,) = Document.bodies
    assert BodyValue.final_feature_id == FeatureId and BodyValue.name == FeatureName
    assert Document.brep is not None and not Document.brep_payloads
    assert not Document.brep.validate(frozenset((BodyValue.id,)))
    Topology = BodyValue.topology
    assert Topology.solid_count == 1
    assert (Topology.face_count, Topology.edge_count, Topology.vertex_count) == (
        6,
        12,
        8,
    )
    Volume = 24.0 * 1.25 * (15.75**2 - 7.5**2) / 2.0
    assert Topology.volume is not None and IsClose(
        Topology.volume, Volume, rel_tol=1e-12
    )


# both normal sinks must fail before any path staging or stream publication
def CheckRefusal(Document: CadDocument, TargetPath: FilePath) -> None:
    (SketchValue,) = Document.sketches
    Invalid = ReplaceValue(
        Document, sketches=(ReplaceValue(SketchValue, suppressed=True),)
    )
    PriorValue = b"existing output"
    StreamValue = BytesIO(PriorValue)
    for Destination in (TargetPath, StreamValue):
        try:
            _ = WriteDoc(
                Invalid,
                Destination,
                destination_format=KPartFormatId,
                allow_carrier=False,
                values={"final_destination": str(TargetPath)},
            )
        except NotFoundError:
            pass
        else:
            raise AssertionError("suppressed thin profile published")
    assert not TargetPath.parent.exists()
    assert StreamValue.getvalue() == PriorValue and StreamValue.tell() == 0


# the isolated hosted phase exercises registry publication before strict independent readback
def RunThinPhase(RootValue: FilePath) -> None:
    Document = MakeThinCase()
    TargetPath = RootValue / (str(Document.metadata["name"]) + KPartSuffix)
    Streams = BytesIO()
    Policy = {"require_native_transfers": True}
    with PatchValue(
        "convert.adapters.solidworks.Core.Writing.EmitNativeMut.ReadTime",
        return_value=1760000000,
    ):
        Written = WriteDoc(Document, TargetPath, allow_carrier=False, values=Policy)
        Named = WriteDoc(
            Document,
            Streams,
            destination_format=KPartFormatId,
            allow_carrier=False,
            values={**Policy, "final_destination": str(TargetPath)},
        )
    RawValue = TargetPath.read_bytes()
    assert RawValue == Streams.getvalue()
    for Result in (Written, Named):
        assert Result.application_usable and Result.vendor_loadable
        assert Result.bytes_written == len(RawValue) and not Result.dropped
        assert Document.capabilities <= Result.native_capabilities
        assert all(Value.mode is TransferMode.KNative for Value in Result.transfers)
    for SourceValue in (TargetPath, Streams.getvalue()):
        CheckSolid(SourceValue, Document.feature_timeline[0].name)
    CheckRefusal(Document, RootValue / "Rejected" / TargetPath.name)


if __name__ == "__main__":
    RunThinPhase(FilePath(Arguments[2]))
