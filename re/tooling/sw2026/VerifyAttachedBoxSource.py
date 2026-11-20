from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(Path(__file__).resolve().parent)]

from ProjectFreecadBox import project
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import ReadBoxSource
from interchange import CadDocument
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


DISCLOSED = {
    "0.21.2": (
        "bfc2aebf050999e5d8eefa0b2d10196af09ed982de6b94c0e2be1f5b9ff54854",
        "25c836424406343439bd3fa9acd82f8e6dbabdae689fe2a799099bf73805aafb",
    ),
    "1.0.2": (
        "3a241aefd40124fed9d414a5ca7fbebb87c863b9e6a9a8e8fd3502743432c978",
        "40a68d097af87a4ca192fe8d0caa227e236547cc1a5e8b95ddba1037eb8dca70",
    ),
    "1.1.4": (
        "157d2fbe911c585748a214ca0b0aa344b8ceef69dd1ac6111ebc837a9068f38c",
        "dba4b4257d5b44c03051121c52d9ffb84e73fe17deae499256d807a129cd8852",
    ),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def old_project(document):
    return project(document, source_labels=True, attached_top=True)


def load_disclosed(folder):
    cases = {}
    for release, (expected_request, expected_source) in DISCLOSED.items():
        raw = (folder / f"recipe-{release}-F14c.json").read_bytes()
        require(sha256(raw).hexdigest() == expected_request, "disclosed neutral request hash differs")
        row = json.loads(raw)["document"]
        document = FromData(row)
        require(
            type(document) is CadDocument and document.source.sha256 == expected_source,
            "disclosed neutral request lost its source identity",
        )
        cases[release] = (document, row)
    return cases


def compare(document):
    original = old_project(document)
    candidate = ReadBoxSource(document)
    fields = {
        "lowered_model": original.model == candidate.ModelValue,
        "properties": all(
            tuple(getattr(original.properties, name).items()) == tuple(getattr(candidate.PropertiesValue, name).items())
            for name in ("SummaryFields", "DocumentFields", "ConfigurationFields")
        ),
        "dimensions": original.dimensions_mm == candidate.DimensionsValue,
        "creation_epoch": original.creation_epoch == candidate.CreationEpoch,
        "parameter_bindings": original.parameter_bindings == candidate.ParameterBindings,
        "body_name": original.source_body_label == candidate.SourceBodyName,
        "feature_name": original.source_feature_label == candidate.SourceFeatureName,
        "geometry": original.geometry == candidate.GeometryValue,
        "units": original.unit_recipe == candidate.UnitsValue,
    }
    require(all(fields.values()), "source projector changed a disclosed value")
    return {
        "equal_fields": sorted(fields),
        "dimensions_mm": list(candidate.DimensionsValue),
        "property_count": len(candidate.PropertiesValue.DocumentFields),
        "support": candidate.ModelValue.support_planes[0].name,
        "native_boss_reversed": candidate.ModelValue.feature_timeline[0].definition.reversed,
        "source_cache_compared": candidate.GeometryValue["source_cache_compared"],
    }


def mutate(document, name):
    data = deepcopy(document)
    feature, = data["feature_timeline"]["$tuple"]
    body, = data["bodies"]["$tuple"]
    model = data["metadata"]["freecad"]
    owners = {row["name"]: row for row in model["objects"]}
    source = feature["definition"]["object_data"]
    fields = source["properties"]
    doc_fields = model["document_properties"]["children"]
    if name == "subelement_support":
        fields["AttachmentSupport"]["children"][0]["children"][0]["attributes"]["sub"] = "Face1"
    elif name == "positive_attachment_offset":
        fields["AttachmentOffset"]["children"][0]["attributes"]["Px"] = "3.0"
    elif name == "unknown_feature_property":
        fields["ExtraLength"] = deepcopy(fields["Length"])
    elif name == "unknown_document_property":
        extra = deepcopy(next(row for row in doc_fields if row["attributes"]["name"] == "Label"))
        extra["attributes"]["name"] = "UnknownLabel"
        doc_fields.append(extra)
    elif name == "foreign_dimension_owner":
        length = next(
            row for row in data["parameters"]["$tuple"] if row["attributes"]["freecad_path"] == "Length"
        )
        length["owner_id"] = body["id"]
    elif name == "unknown_material":
        fields["ShapeMaterial"]["children"][0]["attributes"]["uuid"] = "00000000-0000-0000-0000-000000000000"
    elif name == "foreign_unit_selector":
        selection = next(row for row in doc_fields if row["attributes"]["name"] == "UnitSystem")
        selection["children"][0]["attributes"]["value"] = "1"
    elif name == "populated_string_map":
        model["string_hasher"]["entries"] = ["custom identifier"]
    elif name == "displaced_origin_point":
        owners["Origin001"]["properties"]["Placement"]["children"][0]["attributes"]["Px"] = "1.0"
    elif name == "unknown_release":
        data["source"]["application_version"] = model["program_version"] = "9.9R1 (Git)"
    elif name == "unowned_neutral_plane":
        plane = next(row for row in data["support_planes"]["$tuple"] if row["name"] == "XZ-plane")
        plane["id"] = "freecad:plane:unowned"
    elif name == "inconsistent_object_owner":
        owners[source["name"]]["touched"] = True
        return FromData(data)
    else:
        raise ValueError("unknown source mutation")
    owners[source["name"]].update(source)
    return FromData(data)


def refused(projector, document):
    try:
        projector(document)
    except (ValueError, TypeError, KeyError, OverflowError):
        return True
    return False


def main():
    parser = ArgumentParser(description="Compare the exact disclosed F14c neutral source projectors")
    parser.add_argument("disclosed_neutral_directory", type=Path)
    args = parser.parse_args()
    cases = load_disclosed(args.disclosed_neutral_directory)
    guards = (
        "subelement_support", "positive_attachment_offset", "unknown_feature_property",
        "unknown_document_property", "foreign_dimension_owner", "unknown_material",
        "foreign_unit_selector", "populated_string_map", "displaced_origin_point", "unknown_release",
    )
    source_only = ("unowned_neutral_plane", "inconsistent_object_owner")
    variants = {name: mutate(cases["1.1.4"][1], name) for name in (*guards, *source_only)}
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    comparisons = {}
    for release, (document, _) in cases.items():
        comparisons[release] = {
            "request_sha256": DISCLOSED[release][0],
            "source_sha256": DISCLOSED[release][1],
            "with_shape_cache": compare(document),
            "without_shape_cache": compare(replace(document, brep=None, brep_payloads=())),
        }
    negatives = {
        name: {
            "reference_refused": refused(old_project, document),
            "ported_projector_refused": refused(ReadBoxSource, document),
        }
        for name, document in variants.items()
    }
    require(
        all(negatives[name]["reference_refused"] for name in guards)
        and all(row["ported_projector_refused"] for row in negatives.values()),
        "an invalid source projection was admitted",
    )
    require(not audit.DeniedReads, "source projection attempted runtime input reads")
    print(json.dumps(
        {
            "scope": "disclosed F14c source projections",
            "runtime_input_file_reads": len(audit.DeniedReads),
            "native_application_launches": 0,
            "native_files_generated": 0,
            "comparison": comparisons,
            "rejections": negatives,
        },
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ))


if __name__ == "__main__":
    main()
