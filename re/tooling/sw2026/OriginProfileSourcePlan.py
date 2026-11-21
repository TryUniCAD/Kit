from __future__ import annotations

import math
import secrets
import string

from AuthorCurves import require

SCHEMA = "kit.sw2026.origin-profile-source-input.v1"
DISCLOSED = ("D01", "D02", "D03", "D04")
HIDDEN = ("H01", "H02", "H03", "H04")


def case_row(
    identifier, kind, width, height, depth, orientation, scale, position, child_name
):
    return {
        "id": identifier,
        "name": "OriginView" + identifier,
        "child_name": child_name,
        "part": {
            "kind": kind,
            "width_m": width,
            "height_m": height,
            "depth_m": depth,
            "edit_width_m": width + 0.009137,
            "edit_height_m": height + 0.007291,
        },
        "view": {
            "orientation": orientation,
            "position_m": list(position),
            "scale": scale,
        },
        "view_move_m": [0.003041, -0.001813],
    }


def disclosed_cases():
    return [
        case_row(
            "D01",
            "corner",
            0.033719,
            0.018431,
            0.006247,
            "*Front",
            0.683,
            (0.087413, 0.063917),
            "OriginChildD01",
        ),
        case_row(
            "D02",
            "center",
            0.046783,
            0.021659,
            0.004829,
            "*Right",
            0.812,
            (0.113291, 0.074613),
            "OriginChildD02",
        ),
        case_row(
            "D03",
            "corner",
            0.028417,
            0.037291,
            0.009173,
            "*Top",
            1.137,
            (0.079647, 0.091223),
            "OriginChildD03",
        ),
        case_row(
            "D04",
            "center",
            0.052913,
            0.024827,
            0.005731,
            "*Front",
            0.437,
            (0.141283, 0.105719),
            "ProfilOrigineÉtudeD04",
        ),
    ]


def hidden_cases():
    def length(start, count):
        return (start + secrets.randbelow(count)) / 1e6

    result = []
    for index, identifier in enumerate(HIDDEN):
        token = "".join(secrets.choice(string.ascii_lowercase) for unused in range(10))
        row = case_row(
            identifier,
            "center" if index % 2 else "corner",
            length(29000, 27000),
            length(16000, 22000),
            length(4100, 6500),
            ("*Top", "*Front", "*Right", "*Front")[index],
            length(410000, 510000),
            (length(77000, 42000), length(69000, 34000)),
            "OriginChild" + identifier + token,
        )
        row["view_move_m"] = [length(2100, 1800), -length(1200, 1100)]
        result.append(validate(row))
    return result


def validate(case):
    require(
        set(case) == {"id", "name", "child_name", "part", "view", "view_move_m"},
        "origin source has unexpected input fields",
    )
    require(
        case["id"] in DISCLOSED + HIDDEN and case["name"] == "OriginView" + case["id"],
        "origin source case identity differs",
    )
    require(
        isinstance(case["child_name"], str)
        and 8 <= len(case["child_name"]) <= 80
        and not any(c in case["child_name"] for c in '\\/:*?"<>|'),
        "child basename is outside the ordinary standalone profile",
    )
    part = case["part"]
    require(
        set(part)
        == {"kind", "width_m", "height_m", "depth_m", "edit_width_m", "edit_height_m"}
        and part["kind"] in ("corner", "center"),
        "origin child must use the proven native rectangle author",
    )
    require(
        all(
            type(v) is float and math.isfinite(v) and 0.001 < v < 0.2
            for k, v in part.items()
            if k != "kind"
        ),
        "origin child lengths are outside the locked domain",
    )
    view = case["view"]
    require(
        set(view) == {"orientation", "position_m", "scale"}
        and view["orientation"] in ("*Front", "*Top", "*Right"),
        "origin source needs one ordinary principal view",
    )
    require(
        type(view["scale"]) is float and 0.3 < view["scale"] < 1.5,
        "origin source view scale is outside the locked domain",
    )
    require(
        len(view["position_m"]) == len(case["view_move_m"]) == 2
        and all(
            type(v) is float and math.isfinite(v)
            for v in [*view["position_m"], *case["view_move_m"]]
        ),
        "origin source view vectors differ",
    )
    require(
        all(0.02 < v < 0.18 for v in view["position_m"]) and any(case["view_move_m"]),
        "origin source view position is outside the locked domain",
    )
    return case
