KCoedgeUses = ("coedge", "tcoedge-coedge")

KCoedgeRules: dict[int, tuple[str, ...]] = {
    0: ("ATTRIB_CUSTOM-attrib",),
    2: (),
    3: KCoedgeUses,
    4: KCoedgeUses,
    5: KCoedgeUses,
    6: ("edge", "tedge-edge"),
    8: ("loop",),
    10: ("pcurve",),
}

KEdgeRules: dict[int, tuple[str, ...]] = {
    0: ("ATTRIB_CUSTOM-attrib",),
    2: (),
    3: ("vertex", "tvertex-vertex"),
    5: ("vertex", "tvertex-vertex"),
    7: KCoedgeUses,
    8: ("ellipse-curve", "straight-curve", "intcurve-curve"),
}

KVertexRules: dict[int, tuple[str, ...]] = {
    0: ("ATTRIB_CUSTOM-attrib",),
    2: (),
    3: ("edge", "tedge-edge"),
    5: ("point",),
}

KEntityRefRules: dict[str, dict[int, tuple[str, ...]]] = {
    "transform": {0: ("ATTRIB_CUSTOM-attrib",)},
    "asmheader": {0: ("ATTRIB_CUSTOM-attrib",)},
    "body": {
        0: ("ATTRIB_CUSTOM-attrib",),
        2: (),
        3: ("lump",),
        4: (),
        5: ("transform",),
    },
    "lump": {
        0: ("ATTRIB_CUSTOM-attrib",),
        2: (),
        3: ("lump",),
        4: ("shell",),
        5: ("body",),
    },
    "shell": {
        0: ("ATTRIB_CUSTOM-attrib",),
        2: (),
        3: ("shell",),
        4: (),
        5: ("face",),
        6: (),
        7: ("lump",),
    },
    "face": {
        0: ("ATTRIB_CUSTOM-attrib",),
        2: (),
        3: ("face",),
        4: ("loop",),
        5: ("shell",),
        6: (),
        7: (
            "plane-surface",
            "cone-surface",
            "sphere-surface",
            "torus-surface",
            "spline-surface",
        ),
    },
    "loop": {
        0: ("ATTRIB_CUSTOM-attrib",),
        2: (),
        3: ("loop",),
        4: ("coedge", "tcoedge-coedge"),
        5: ("face",),
    },
    "coedge": KCoedgeRules,
    "tcoedge-coedge": {**KCoedgeRules, 13: ()},
    "edge": KEdgeRules,
    "tedge-edge": KEdgeRules,
    "vertex": KVertexRules,
    "tvertex-vertex": KVertexRules,
    "spline-surface": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "intcurve-curve": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "pcurve": {0: ("ATTRIB_CUSTOM-attrib",), 2: (), 4: ("intcurve-curve",)},
    "point": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "plane-surface": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "sphere-surface": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "torus-surface": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "cone-surface": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "ellipse-curve": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "straight-curve": {0: ("ATTRIB_CUSTOM-attrib",), 2: ()},
    "ATTRIB_CUSTOM-attrib": {
        0: (),
        2: ("ATTRIB_CUSTOM-attrib",),
        3: ("ATTRIB_CUSTOM-attrib",),
        4: (
            "body",
            "face",
            "edge",
            "coedge",
            "tedge-edge",
            "tcoedge-coedge",
        ),
    },
}
