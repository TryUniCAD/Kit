from io import BytesIO
from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature
from tests.Convert.Solidworks.PlainWriting.ReversePrep.MakePrepDoc import MakePrepDoc
from tests.Convert.Solidworks.PlainWriting.ReversePrep.PrepCase import PrepCase
from tests.Convert.Solidworks.PlainWriting.ReversePrep.ReadPrepCases import (
    ReadPrepCases,
)


# full generated archives must retain signed intent and their solved body through the public sdk
@MarkTests.parametrize("CaseValue", ReadPrepCases())
def CheckPrepRead(CaseValue: PrepCase) -> None:
    Document = MakePrepDoc(CaseValue)
    Candidate = PrepareNative(
        Document,
        BytesIO(),
        1795737600,
        WriteOptions(
            values={
                "final_destination": rf"C:\KitReverseResearch\{CaseValue.NameValue}.SLDPRT"
            }
        ),
    )
    assert Candidate.PlanValue.IsReversed is CaseValue.IsReversed
    assert Candidate.BossValue.EndValue.FieldsValue["f8c"] == int(CaseValue.IsReversed)
    StartValue = Candidate.BossValue.EndValue.FieldsValue["f140"]
    assert isinstance(StartValue, ArchiveNode) and StartValue.FieldsValue["t"] == 0
    Restored = OpenDocument(
        BytesIO(Candidate.BytesValue), source_format="solidworks.sldprt"
    )
    Solid = Restored.bodies[0]
    assert Solid.topology.valid is None and Solid.topology.volume is not None
    assert Solid.topology.solid_count == Solid.topology.shell_count == 1
    assert Restored.brep is not None
    Restored.AssertValid()
    assert IsClose(Solid.topology.volume, CaseValue.VolumeMm, rel_tol=1e-10)
    assert Solid.topology.bounding_box is not None
    Bounds = Solid.topology.bounding_box
    assert IsClose(
        Bounds.minimum.z,
        -CaseValue.DepthMm if CaseValue.IsReversed else 0,
        abs_tol=1e-9,
    )
    assert IsClose(
        Bounds.maximum.z, 0 if CaseValue.IsReversed else CaseValue.DepthMm, abs_tol=1e-9
    )
    Centroid = CastValue(
        tuple[float, ...], Solid.attributes["solidworks.body_centroid_mm"]
    )
    assert len(Centroid) == 3
    assert all(
        IsClose(Actual, Expected, abs_tol=1e-9)
        for Actual, Expected in zip(Centroid, CaseValue.CentroidMm, strict=True)
    )
    Owner = next(
        Feature
        for Feature in Restored.feature_timeline
        if Feature.id == Solid.final_feature_id
    )
    assert isinstance(Owner.definition, ExtrudeFeature)
    assert Owner.definition.reversed is CaseValue.IsReversed
    assert Owner.definition.length is not None
    assert IsClose(
        float(Owner.definition.length.value), CaseValue.DepthMm, abs_tol=1e-9
    )
    assert CadDocument.from_json(Restored.to_json()) == Restored
