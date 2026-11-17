from __future__ import annotations

from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# identical authored dimensions keep the cold scope experiment independent of geometry changes
def MakeBlindCutInput(ScopeValue: str) -> dict[str, object]:
    Request = MakePartInput(
        [[-0.0319, -0.0241], [0.0267, -0.0241], [0.0267, 0.0193], [-0.0319, 0.0193]],
        0.0157,
        "Eccentric Pocket Discovery",
    )
    Request["blind_cut_discovery"] = {
        "sketch_name": "PocketSketch",
        "feature_name": "BlindPocket",
        "center_m": [0.0097, -0.0073],
        "radius_m": 0.00641,
        "depth_m": 0.00483,
        "dimension_text_point_m": [0.0211, 0.0107, 0.0],
        "scope": ScopeValue,
    }
    return Request
