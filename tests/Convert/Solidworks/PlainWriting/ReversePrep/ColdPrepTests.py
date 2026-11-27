from io import BytesIO
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.PlainWriting.ReversePrep.PrepCase import PrepCase
from tests.Convert.Solidworks.PlainWriting.ReversePrep.ReadPrepCases import (
    ReadPrepCases,
)


# complete cold source state must survive restoration and regeneration without dropping its signed extent
@MarkTests.parametrize("CaseValue", ReadPrepCases())
def CheckColdPrep(CaseValue: PrepCase) -> None:
    Source = (
        FilePath(__file__).resolve().parents[5]
        / "re/solidworks/DecodedPromotion20261127/Evidence"
        / (CaseValue.NameValue + ".SLDPRT")
    )
    Document = OpenDocument(Source)
    Restored = CadDocument.from_json(Document.to_json())
    Candidate = PrepareNative(
        Restored,
        BytesIO(),
        1795737600,
        WriteOptions(
            values={
                "final_destination": rf"C:\KitReverseResearch\{CaseValue.NameValue}.SLDPRT"
            }
        ),
    )
    assert Candidate.BytesValue == Source.read_bytes()
    assert Candidate.PlanValue.IsReversed is CaseValue.IsReversed
