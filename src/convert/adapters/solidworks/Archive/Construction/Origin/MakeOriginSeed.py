from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# origin profile data must own complete empty contour state and its actual sketch reference before local geometry is inserted
def MakeOriginSeed(
    SketchValue: ArchiveNode, Reference: ArchiveNode, FrameValue: PlaneFrame
) -> dict[str, object]:
    return {
        "f390": 0,
        "orig_dim_feature": None,
        "f3dc": 0,
        "pd_f80": SketchValue,
        "d5c0": {"n2a8": 0, "f2a8": [], "f2b0": 0},
        "ca30": {
            "n238": 0,
            "f238": [],
            "f10": 3,
            "f198": {"empty": 1},
            "f168": {"n": 0, "items": []},
            "f188": {"elem": 0},
        },
        "f3e0": 100000,
        "f3e8": {"n": 0, "items": []},
        "f3b8": None,
        "write_ref": 1,
        "pd_f78": Reference,
        "pd_ff0": FrameXform(FrameValue),
        "pd_has_fe8": 0,
        "pd_f100": 4,
        "pd_f110": None,
        "pd_f11c": -1 & ~6,
        "pd_f118": 0,
        "pd_f2a0": 101,
        "f3c0": 0,
        "f388": None,
        "pd_f128": {"n": 0, "items": []},
        "pd_f148": {"n": 0, "items": []},
        "f42c": 0,
    }
