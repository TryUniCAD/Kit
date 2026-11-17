from __future__ import annotations

from uuid import UUID

from Core import Obj
from builders.Metadata import boolean, integer
from builders.Model import feature, object_list


def _drawing(owner):
    if not isinstance(owner, Obj) or owner.cls != "moDrawing_c":
        raise ValueError("empty drawing managers require their actual model owner")


def _feature_filetime(created_at):
    seconds = integer(created_at, "drawing creation time")
    value = (seconds + 11644473600) * 10_000_000
    lower, upper = value & 0xFFFFFFFF, value >> 32
    return {
        "f2a0": lower - (1 << 32) if lower & 0x80000000 else lower,
        "f2a4": upper - (1 << 32) if upper & 0x80000000 else upper,
    }


def drawing_options(*, auto_dim_text_link):
    link = boolean(auto_dim_text_link, "automatic dimension text link")
    return 0x100 | int(link)


def empty_layer_manager(*, owner):
    _drawing(owner)
    mask = Obj("moLayerMask_c", {"f08": {"n": 0, "f18": 0, "data": b""}})
    return Obj("moLayerMgr_c", {
        "n": 0, "layers": [], "f08": None, "f30": owner, "f20": mask, "f38": -1,
    })


def empty_block_manager(*, owner, block_identity, created_at, date_code, parasolid_version):
    _drawing(owner)
    if not isinstance(block_identity, UUID) or block_identity.version != 4:
        raise ValueError("a fresh drawing block manager requires an independently allocated UUID4")
    result = feature(
        cls="moSketchBlockMgr_c", name="Sketch Blocks", owner=owner,
        allocator=None, date_code=date_code, parasolid_version=parasolid_version,
    )
    result.f.update({
        **_feature_filetime(created_at),
        "f18": None, "f0c": 0, "f380": block_identity.bytes_le,
        "blocks": {"f18": 0, "f30": result, "n70": 0, "f68": [], "n98": 0, "f90": []},
    })
    return result


def empty_drawing_tail(*, owner, active_sheet, auto_dim_text_link, block_identity, created_at, date_code, parasolid_version):
    _drawing(owner)
    if not isinstance(active_sheet, Obj) or active_sheet.cls != "moDrSheet" or active_sheet.get("owner") is not owner:
        raise ValueError("drawing suffix requires its generated active sheet")
    return {
        "fe80": empty_block_manager(
            owner=owner, block_identity=block_identity, created_at=created_at,
            date_code=date_code, parasolid_version=parasolid_version,
        ),
        "fed0": empty_layer_manager(owner=owner),
        "f1430": active_sheet, "f143c": 1,
        "f1444": drawing_options(auto_dim_text_link=auto_dim_text_link),
        "f1458": None, "f16a8": Obj("moDrwCompPropMgr_c", {"f18": owner, "n10": 0, "f08": []}),
        "n1568": 0, "f1560": [], "n1578": 0, "f1570": [], "n1740": 0,
        "f14f8": {"n": 0, "items": [], "f38": 1},
        "zero_instance_blocks": object_list(), "n1538": 0, "f1538": [],
    }
