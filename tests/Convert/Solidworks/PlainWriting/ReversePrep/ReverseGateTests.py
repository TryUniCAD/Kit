from dataclasses import replace as CopyData
from hashlib import sha256 as HashBytes
from io import BytesIO
from typing import cast as CastValue

from pytest import mark as MarkTests, raises as RaisesError

from convert import write_document as WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.Features.FeatureExtrude import ExtrudeFeature
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc


# native evidence for a forward archive must never authorize publication of changed reverse bytes
@MarkTests.parametrize("RoleName", ("Skew", "Step"))
@MarkTests.parametrize("IsDirect", (False, True))
def CheckMeasGuard(RoleName: str, IsDirect: bool) -> None:
    Document, Envelope, Digest = MeasurePlainDoc(RoleName)
    Settings = {
        "final_destination": rf"C:\KitSdkCandidates\{Document.metadata['name']}.SLDPRT",
        KPartMeasureOpt: Envelope,
    }
    Forward = PrepareNative(
        Document, BytesIO(), 1794973072, WriteOptions(values=Settings)
    )
    assert HashBytes(Forward.BytesValue).hexdigest() == Digest
    Feature = Document.feature_timeline[0]
    assert isinstance(Feature.definition, ExtrudeFeature)
    Reverse = CopyData(
        Document,
        feature_timeline=(
            CopyData(Feature, definition=CopyData(Feature.definition, reversed=True)),
        ),
    )
    Candidate = PrepareNative(
        Reverse, BytesIO(), 1794973072, WriteOptions(values=Settings)
    )
    assert (
        Candidate.PlanValue.IsReversed
        and HashBytes(Candidate.BytesValue).hexdigest() != Digest
    )
    Target = BytesIO()
    with RaisesError(ValueError, match="no unique exact native measurement"):
        if IsDirect:
            _ = SldprtWriter().write(Reverse, Target, WriteOptions(values=Settings))
        else:
            _ = WriteDocument(
                Reverse, Target, destination_format="solidworks.sldprt", values=Settings
            )
    assert Target.getvalue() == b""


# reversed construction still requires an unambiguous boolean single blind direction
@MarkTests.parametrize("CaseName", ("boolean", "symmetric", "direction", "offset"))
def CheckPrepLimits(CaseName: str) -> None:
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from interchange.Records.RecordParameter import ParameterValue
    from interchange.Enums.EnumValues import ValueKind

    Document, _, _ = MeasurePlainDoc("Skew")
    Feature = Document.feature_timeline[0]
    assert isinstance(Feature.definition, ExtrudeFeature)
    Definition = CopyData(Feature.definition, reversed=True)
    if CaseName == "boolean":
        Definition = CopyData(Definition, reversed=CastValue(bool, 1))
    elif CaseName == "symmetric":
        Definition = CopyData(Definition, symmetric=True)
    elif CaseName == "direction":
        Definition = CopyData(Definition, direction=SpaceVector(0.0, 0.0, -1.0))
    else:
        Definition = CopyData(
            Definition, offset=ParameterValue(1.0, ValueKind.KLength, "mm")
        )
    Changed = CopyData(
        Document, feature_timeline=(CopyData(Feature, definition=Definition),)
    )
    Settings = WriteOptions(
        values={
            "final_destination": rf"C:\KitSdkCandidates\{Document.metadata['name']}.SLDPRT"
        }
    )
    with RaisesError(ValueError):
        _ = PrepareNative(Changed, BytesIO(), 1794973072, Settings)
