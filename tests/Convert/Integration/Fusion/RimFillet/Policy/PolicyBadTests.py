from hashlib import sha256 as HashData
from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaiseError

from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPolicy import (
    CheckRimPolicy,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


# actual encoded corruptions must reopen before policy refusal can prove the native boundary is guarded
@TestMark.parametrize(
    "ModeName",
    (
        "role",
        "unit",
        "expression",
        "owner",
        "reciprocal",
        "allocator",
        "selected_owner",
        "selected_alias",
        "selected_body",
        "radius_alias",
        "variable_mode",
        "scope_mode",
        "history_join",
        "dynamic_owner",
        "cached_radius",
        "recipe_face",
        "cache_distribution",
    ),
)
def CheckPolicyBad(ModeName: str) -> None:
    Folder = (
        FilePath(__file__).resolve().parents[6]
        / "re/Fusion/DecodedPromotion20261127/RimFilletPolicy"
    )
    Receipt = LoadJson(
        (
            Folder
            / (
                "ExtraCounterReceipt.json"
                if ModeName == "cache_distribution"
                else "ReceiptV2.json"
            )
        ).read_text()
    )
    Entry = next(
        Value
        for Value in Receipt[
            "rows" if ModeName == "cache_distribution" else "counterexamples"
        ]
        if Value["mode"] == ModeName
    )
    Encoded = (Folder / "Counterexamples" / (ModeName + ".f3d")).read_bytes()
    assert HashData(Encoded).hexdigest() == Entry["sha256"] and Entry["encoded"]
    Model = ReadDocument(Encoded)
    Graph = BuildGraph(Model)
    with RaiseError((ValueError, KeyError)):
        Context = ReadRimContext(Graph)
        CheckRimPolicy(Model, Graph, Context)
