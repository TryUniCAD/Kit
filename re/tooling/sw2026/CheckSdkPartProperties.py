from __future__ import annotations

from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from builders.PartTextProperties import make_property_streams
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.MakePolygonBlindPart import MakePolygonPart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import ProjectBlind
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import ReadLineLoop
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(name) for name in ("utf-8", "latin-1", "utf-16-le"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def extract(document):
    require(type(document) is CadDocument and len(document.configurations) == 1
            and set(document.metadata) <= {"name", "document_summary", "custom_properties"},
            "unsupported text property neutral structure")
    original, = document.configurations
    require(set(original.attributes) <= {"custom_properties"}, "unsupported configuration property structure")
    summary = document.metadata.get("document_summary", {})
    model = document.metadata.get("custom_properties", {})
    configured = original.attributes.get("custom_properties", {})
    modeled = replace(document, configurations=(replace(original, attributes={}),),
                      metadata={"name": document.metadata["name"]})
    return modeled, PartTextInput(summary, model, configured)


def validate_rejections(builder, modeled, recipe, inputs):
    cases = {
        "unbound_summary": replace(inputs, SummaryFields={"subject_address": "unbound"}),
        "duplicate_name": replace(inputs, DocumentFields={"ScopeName": "One", "scopename": "Two"}),
        "non_text": replace(inputs, DocumentFields={"NumericInput": 7.0}),
        "linked_text": replace(inputs, DocumentFields={"Reference": ' $pRp:"PartNumber"'}),
        "equation": replace(inputs, ConfigurationFields={"Formula": "=6*7"}),
        "invalid_xml": replace(inputs, SummaryFields={"title": "A\u0000B"}),
        "multiline": replace(inputs, ConfigurationFields={"Multi": "one\ntwo"}),
        "unsupported_name": replace(inputs, DocumentFields={"9Title": "value"}),
    }
    rejected = []
    for label, fault in cases.items():
        try:
            builder(modeled, replace(recipe, PropertiesValue=fault))
        except (ValueError, TypeError) as error:
            rejected.append({"case": label, "error": str(error)})
        else:
            raise ValueError("unsupported property unexpectedly generated: " + label)
    return rejected


def main():
    modeled, inputs = extract(FromData(REQUEST["document"]))
    if REQUEST["profile"] == "polygon":
        plan, builder = ProjectBlind(modeled, ReadLineLoop), MakePolygonPart
    elif REQUEST["profile"] == "circle":
        plan, builder = ProjectCircle(modeled), MakeCirclePart
    else:
        raise ValueError("unrecognized property probe feature profile")
    recipe = MakePartRecipe(plan, REQUEST["created_at"])
    recipe = BindPartIntent(modeled, plan, recipe, recipe.OutputValue)
    first = builder(modeled, recipe)
    result = builder(modeled, replace(recipe, PropertiesValue=inputs))
    empty = builder(modeled, replace(recipe, PropertiesValue=PartTextInput({}, {}, {})))
    reference = make_property_streams(inputs.SummaryFields, inputs.DocumentFields, inputs.ConfigurationFields)
    expected = {**first.StreamsValue, **reference}
    parsed = SldprtArchive.FromBytes(result.BytesValue)
    require(first.BytesValue == empty.BytesValue and len(first.StreamsValue) == 10,
            "empty properties changed the existing ordinary model")
    require(parsed.Streams == result.StreamsValue == expected and BuildSldprt(expected, FormatVersion=4) == result.BytesValue,
            "property promotion differs from the independent reference composer")
    rejected = validate_rejections(builder, modeled, recipe, inputs)
    return {"schema": "kit.sw2026.sdk-part-property-promotion.v1",
            "passed": True, "input_profile": REQUEST["profile"], "file_bytes": len(result.BytesValue),
            "file_sha256": sha256(result.BytesValue).hexdigest(),
            "base_file_sha256": sha256(first.BytesValue).hexdigest(), "base_file_identical_with_empty_input": True,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "native_output_stream_count": len(result.StreamsValue),
            "stream_sha256": {key: sha256(value).hexdigest() for key, value in result.StreamsValue.items()},
            "rejections": rejected}


print(json.dumps(main(), ensure_ascii=False, sort_keys=True, allow_nan=False))
