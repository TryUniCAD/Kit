from json import dumps as DumpJson

from tests.Convert.Solidworks.KeywordModels.RunKeywordModel import RunKeyModel

# each rejection starts with an ordinary row so only the requested rule can fail
KPlainFeature: dict[str, object] = {
    "id": 17,
    "name": "Test profile",
    "kind": "moProfileFeature_c",
    "tag": "Sketch",
}

# malformed feature shapes must fail before any stream bytes reach the caller
KShapeRejects: tuple[tuple[list[dict[str, object]], bytes], ...] = (
    ([{**KPlainFeature, "children": [21]}], b"identify actual emitted features"),
    ([{**KPlainFeature, "children": [17, 21]}], b"single child grammar"),
    ([KPlainFeature, KPlainFeature], b"identifiers must be unique"),
    ([{**KPlainFeature, "tag": "Reference"}], b"unsupported keyword feature tag"),
    (
        [{**KPlainFeature, "kind": None, "dissectable": True}],
        b"requires its native revolve angle",
    ),
    ([{**KPlainFeature, "dissectable": 1}], b"require explicit booleans"),
    (
        [
            KPlainFeature,
            {
                "id": 18,
                "name": "Cut",
                "kind": None,
                "tag": "Extrusion",
                "children": [17],
                "dimensions": [{"name": "D2", "value": 2}],
            },
        ],
        b"actual single D1 dimension",
    ),
)

# invalid dimension values must reach the distinct numeric and suffix policy checks
KValueRejects: tuple[tuple[list[dict[str, object]], bytes], ...] = (
    (
        [{**KPlainFeature, "dimensions": [{"name": "D1", "value": 2, "unit": "in"}]}],
        b"unit suffix is classified only",
    ),
    (
        [
            {
                **KPlainFeature,
                "dimensions": [{"name": "D1", "value": 2, "unit": "degree"}],
            }
        ],
        b"degree suffix requires an ordinary revolve feature",
    ),
    (
        [{**KPlainFeature, "dimensions": [{"name": "D1", "value": float("inf")}]}],
        b"outside its finite authored domain",
    ),
)

# ordinary angular rows must bind the one authored angle to its actual driver name and unit
KAngularFeature: dict[str, object] = {
    "id": 18,
    "name": "Revolved boss",
    "kind": "Revolve",
    "tag": "Feature",
}

# a typed sketch leaves the angular owner responsible for rejecting malformed drivers
KAngularDimensions: tuple[list[dict[str, object]], ...] = (
    [],
    [{"name": "D1", "value": 47.25}],
    [{"name": "D2", "value": 47.25, "unit": "degree"}],
    [{"name": "D1", "value": 47.25, "unit": "degree"}, {"name": "D2", "value": 2}],
)


# the separate writer must expose the diagnostic without publishing a partial index
def TestKeyRejects() -> None:
    AngularRejects = tuple(
        (
            [KPlainFeature, {**KAngularFeature, "dimensions": DimensionValues}],
            b"ordinary revolve keyword requires its single D1 degree driver",
        )
        for DimensionValues in KAngularDimensions
    )
    for FeatureValues, Diagnostic in (*KShapeRejects, *KValueRejects, *AngularRejects):
        InputValue = {
            "name": "Malformed keyword case",
            "timestamp": 1423956723,
            "configurations": [{"id": 0, "name": "Config", "material": ""}],
            "features": FeatureValues,
        }
        Outcome = RunKeyModel("write", DumpJson(InputValue).encode("utf-8"))
        assert Outcome.returncode != 0, Outcome.stdout
        assert Diagnostic in Outcome.stderr, Outcome.stderr
        assert Outcome.stdout == b""
