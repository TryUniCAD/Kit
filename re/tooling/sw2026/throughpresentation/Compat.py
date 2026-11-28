import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def authored(name, width, height, depth):
    from interchange import CadDocument
    from interchange.Records.RecordSource import CadSource
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from interchange.geometry.Models.SupportPlane import SupportPlane
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.Sketch import Sketch, SketchEntity
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.Features.FeatureStep import FeatureStep
    from interchange.Features.FeatureExtrude import ExtrudeFeature
    from interchange.Features.FeatureBody import DesignBody

    points = ((0.0, 0.0), (width, 0.0), (width, height), (0.0, height))
    entities = tuple(
        SketchEntity(
            "edge/" + str(index),
            "line",
            LineGeometry(
                PlaneVector(*points[index]), PlaneVector(*points[(index + 1) % 4])
            ),
        )
        for index in range(4)
    )
    sketch = Sketch(
        "sketch/profile",
        "AuthoredProfile",
        "plane/front",
        entities,
        closed_profile_entity_ids=(tuple(value.id for value in entities),),
    )
    length = ParameterValue(depth, "length", "mm")
    feature = FeatureStep(
        "feature/boss",
        "AuthoredBoss",
        "extrusion",
        0,
        sketch_id=sketch.id,
        parameter_ids=("parameter/depth",),
        operation="create",
        definition=ExtrudeFeature(length),
    )
    return CadDocument(
        CadSource("kit-neutral", "<authored-in-memory>", "0" * 64),
        (Configuration("configuration/default", "AuthoredDefault", True),),
        (Parameter("parameter/depth", "D1", length, "driving", owner_id=feature.id),),
        (SupportPlane("plane/front", "Front Plane", Transform()),),
        (sketch,),
        (),
        (feature,),
        (DesignBody("body/one", feature.name, feature.id),),
        metadata={"name": name},
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--variant", type=int, choices=(0, 1), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.root / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
        MakeBlindPart,
    )
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import (
        ProjectPlain,
    )
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import (
        MakePartRecipe,
    )
    from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import (
        IndexFeatures,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Presentation.RootOrder import (
        ReadRootOrder,
    )

    name = "CompatPlain" + str(args.variant)
    size = ((41.37, 23.91, 14.27), (57.73, 36.19, 22.61))[args.variant]
    document = authored(name, *size)
    candidate = MakeBlindPart(
        document,
        MakePartRecipe(ProjectPlain(document), 1795000200 + args.variant * 100),
    )
    link = NativeLink(
        candidate.ConfigValue,
        candidate.ResolvedValue,
        "Contents/Config-0",
        "Contents/Config-0-ResolvedFeatures",
    )
    ordered = ReadRootOrder(link, IndexFeatures(link))
    opened = open_document(
        candidate.BytesValue, include_brep=False, include_tessellation=False
    )
    opened.assert_valid()
    tree = opened.metadata["solidworks.typed_resolved_semantics"]["native_tree"]
    if tree["status"] != "ordinary_default_profile" or len(ordered) != 19:
        raise ValueError("existing two-argument ordinary caller changed")
    encoded = opened.to_json(indent=None).encode()
    result = {
        "status": tree["status"],
        "variant": args.variant,
        "generated_sha256": sha256(candidate.BytesValue).hexdigest(),
        "public_document_sha256": sha256(encoded).hexdigest(),
        "ordered_root_ids": tuple(value.FieldsValue["f08"] for value in ordered),
        "two_argument_caller_passed": True,
        "native_oracle_used": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
