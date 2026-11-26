from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


# explicit coordinates distinguish native mapping state from a generated cuboid without mapping
def StageMapDraft(Author: AuthorState) -> None:
    BoxValue = Author.MakeGroup(
        "BBoxValue",
        {
            "min": {"x": 0.125, "y": 0.25, "z": 0.5},
            "max": {"x": 1.75, "y": 2.0, "z": 2.5},
        },
    )
    Fields = {
        "axis": {"x": 0.0, "y": 0.0, "z": 1.0},
        "bakedTransformInGeometry": {"identity": True},
        "textureMappingBoundingBox": [BoxValue],
        "textureMappingTransform": {"identity": True},
    }
    Author.Allocate("mapping_asm", "ASMTextureMapping", Fields=dict(Fields))
    Author.Allocate(
        "mapping_wood",
        "ProceduralWoodTextureMapping",
        Fields=dict(
            Fields,
            bordFaceAxis={"x": 1.0, "y": 0.0, "z": 0.0},
            origin={"x": 0.4375, "y": 0.625, "z": 0.8125},
            originInitilized=True,
        ),
    )
    Author.Allocate(
        "mapping_layers",
        "LayeredTextureMapping",
        Fields=dict(
            Fields,
            activeLayer=0,
            layers=[
                {"key": 2, "value": Author.Reference("mapping_asm")},
                {"key": 3, "value": Author.Reference("mapping_wood")},
            ],
        ),
    )
