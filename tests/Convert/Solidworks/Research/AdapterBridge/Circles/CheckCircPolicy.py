from dataclasses import replace as ReplaceValue
from io import BytesIO
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import write_document as WriteDoc
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature


# unsupported circle intent must fail both public selection and direct emission before changing caller destinations
def CheckCircPolicy(DocumentValue: CadDocument, TargetPath: FilePath) -> None:
    FeatureValue = DocumentValue.feature_timeline[0]
    DefinitionValue = CastValue(ExtrudeFeature, FeatureValue.definition)
    BeforeValue = TargetPath.read_bytes()
    VariantsValue = (
        ReplaceValue(
            DocumentValue,
            metadata={**DocumentValue.metadata, "properties": {"authored": "value"}},
        ),
        ReplaceValue(
            DocumentValue,
            source=ReplaceValue(DocumentValue.source, attributes={"authored": "value"}),
        ),
        ReplaceValue(
            DocumentValue,
            feature_timeline=(
                ReplaceValue(
                    FeatureValue,
                    definition=ReplaceValue(
                        DefinitionValue,
                        end_condition=ExtrudeEnd.KMidPlane,
                        symmetric=True,
                    ),
                ),
            ),
        ),
        ReplaceValue(
            DocumentValue,
            feature_timeline=(
                ReplaceValue(
                    FeatureValue,
                    definition=ReplaceValue(
                        DefinitionValue, reversed=not DefinitionValue.reversed
                    ),
                ),
            ),
        ),
    )
    for InputValue in VariantsValue:
        assert not SldprtWriter().supports(InputValue, TargetPath)
        try:
            _ = WriteDoc(
                InputValue,
                TargetPath,
                destination_format="solidworks.sldprt",
                overwrite=True,
                allow_carrier=False,
            )
        except NotFoundError:
            pass
        else:
            raise AssertionError("public circle writing admitted unqualified intent")
        StreamValue = BytesIO(b"preserved")
        try:
            _ = SldprtWriter().write(
                InputValue,
                StreamValue,
                WriteOptions(values={"final_destination": str(TargetPath)}),
            )
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("direct circle emission bypassed the admission gate")
        assert StreamValue.getvalue() == b"preserved"
    assert TargetPath.read_bytes() == BeforeValue
