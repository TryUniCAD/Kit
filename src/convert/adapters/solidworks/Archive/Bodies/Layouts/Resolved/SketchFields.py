from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KSketchFields = MappingProxyType(
    {
        "sgLineHandle": (NativeField("Base", "sk.sgEntHandle.Serialize"),),
        "sgPointHandle": (NativeField("Base", "sk.sgEntHandle.Serialize"),),
        "sgSketch": (
            NativeField(
                "Array",
                "points",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "kind", "u16"),
                    NativeField("Embed", "point", "sk.sgPoint.FUN_4c58f910"),
                ),
                CountValue="npoints",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "lines",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "flags", "u16"),
                    NativeField("Embed", "line", "sk.sgLine.FUN_4c58ac90"),
                ),
                CountValue="nlines",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "texts",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch texts"),),
                CountValue="ntexts",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "hatches",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch hatches"),),
                CountValue="nhatches",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "arcs",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch arcs"),),
                CountValue="narcs",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "ellipses",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch ellipses"),),
                CountValue="nellipses",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "parabolas",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch parabolas"),),
                CountValue="nparabolas",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "splines",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch splines"),),
                CountValue="nsplines",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "planes",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch planes"),),
                CountValue="nplanes",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "cylinders",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch cylinders"),),
                CountValue="ncylinders",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "spheres",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch spheres"),),
                CountValue="nspheres",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "cones",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch cones"),),
                CountValue="ncones",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "parametric",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch parametric"),),
                CountValue="nparametric",
                ModeValue="Positive",
            ),
            NativeField("Embed", "dims", "sk.sgSketch.FUN_4c5a0f00"),
            NativeField(
                "Array",
                "offsets",
                "u16",
                BodyValue=(NativeField("Fail", "alternate sgSketch offsets"),),
                CountValue="noffsets",
            ),
            NativeField(
                "Array",
                "sketch_offsets",
                "u16",
                BodyValue=(NativeField("Fail", "alternate sgSketch sketch_offsets"),),
                CountValue="nskoffsets",
            ),
            NativeField(
                "Array",
                "styled",
                "u16",
                BodyValue=(NativeField("Fail", "alternate sgSketch styled"),),
                CountValue="nstyled",
            ),
            NativeField(
                "Array",
                "intersections",
                "u16",
                BodyValue=(NativeField("Fail", "alternate sgSketch intersections"),),
                CountValue="nintersections",
            ),
            NativeField("Scalar", "f12c", "u16"),
            NativeField("Scalar", "f128", "u16"),
            NativeField("Scalar", "f130", "i32"),
            NativeField("Embed", "f140", "sk.sgCreationIDs.FUN_4c5864f0"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "alternate sgSketch Branch"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        (
                            "lookup_or",
                            ("context",),
                            ("literal", "conditions"),
                            ("literal", 0),
                        ),
                        ("literal", 2),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "f37c", "u16"),
            NativeField("Scalar", "f188", "u16"),
            NativeField("Scalar", "f18c", "u16"),
            NativeField("Scalar", "f190", "u16"),
            NativeField(
                "Branch",
                "",
                ModeValue="Expression",
                ExpressionValue=(
                    "And",
                    (
                        "Not",
                        (
                            "select",
                            ("compare", ("Eq",), ("literal", 2), ("literal", 0)),
                            (
                                "compare",
                                ("Eq",),
                                (
                                    "lookup_or",
                                    ("context",),
                                    ("literal", "conditions"),
                                    ("literal", 0),
                                ),
                                ("literal", 0),
                            ),
                            (
                                "compare",
                                ("NotEq",),
                                (
                                    "BitAnd",
                                    (
                                        "lookup_or",
                                        ("context",),
                                        ("literal", "conditions"),
                                        ("literal", 0),
                                    ),
                                    ("literal", 2),
                                ),
                                ("literal", 0),
                            ),
                        ),
                    ),
                    (
                        "Not",
                        (
                            "select",
                            ("compare", ("Eq",), ("literal", 1), ("literal", 0)),
                            (
                                "compare",
                                ("Eq",),
                                (
                                    "lookup_or",
                                    ("context",),
                                    ("literal", "conditions"),
                                    ("literal", 0),
                                ),
                                ("literal", 0),
                            ),
                            (
                                "compare",
                                ("NotEq",),
                                (
                                    "BitAnd",
                                    (
                                        "lookup_or",
                                        ("context",),
                                        ("literal", "conditions"),
                                        ("literal", 0),
                                    ),
                                    ("literal", 1),
                                ),
                                ("literal", 0),
                            ),
                        ),
                    ),
                    (
                        "Not",
                        (
                            "select",
                            ("compare", ("Eq",), ("literal", 4), ("literal", 0)),
                            (
                                "compare",
                                ("Eq",),
                                (
                                    "lookup_or",
                                    ("context",),
                                    ("literal", "conditions"),
                                    ("literal", 0),
                                ),
                                ("literal", 0),
                            ),
                            (
                                "compare",
                                ("NotEq",),
                                (
                                    "BitAnd",
                                    (
                                        "lookup_or",
                                        ("context",),
                                        ("literal", "conditions"),
                                        ("literal", 0),
                                    ),
                                    ("literal", 4),
                                ),
                                ("literal", 0),
                            ),
                        ),
                    ),
                ),
            ),
            NativeField("Embed", "f448", "moLineViz_c.Serialize.0"),
            NativeField("Scalar", "f568", "i32"),
            NativeField("Embed", "f570", "mgPoint_c.restore"),
            NativeField("Scalar", "f56c", "u32"),
            NativeField("Scalar", "f578", "i32"),
            NativeField(
                "Array",
                "tools",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch tools"),),
                CountValue="ntools",
                ModeValue="Positive",
            ),
            NativeField("Embed", "f590", "sk.moSketchRelMgr_c.FUN_4c6035c0"),
            NativeField(
                "Array",
                "blocks",
                "i32",
                BodyValue=(NativeField("Fail", "alternate sgSketch blocks"),),
                CountValue="nblocks",
                ModeValue="Positive",
            ),
            NativeField("Embed", "coinc", "sk.pnt3DcoincMap_c.FUN_4b9611e0"),
            NativeField("Node", "f5d8", "suObList"),
            NativeField(
                "Array",
                "silhouettes",
                "u16",
                BodyValue=(NativeField("Fail", "alternate sgSketch silhouettes"),),
                CountValue="nsilhouettes",
            ),
            NativeField("Embed", "f580", "sk.sgBlockManager.FUN_4c90b810"),
            NativeField("Embed", "f598", "sk.sgLoopManager.FUN_4c58cf30"),
            NativeField("Embed", "f588", "sk.sgSlotManager_c.FUN_4c59a5f0"),
            NativeField("Scalar", "f134", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Fail", "alternate sgSketch Branch"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "bool",
                    ("lookup_or", ("context",), ("literal", "ctx874"), ("literal", 0)),
                ),
            ),
        ),
        "sk.EquationVarValueMap_c.FUN_4c339ca0": (
            NativeField(
                "Array",
                "vars",
                "Count",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.EquationVarValueMap_c.FUN_4c339ca0 vars"
                    ),
                ),
                CountValue="n",
            ),
        ),
        "sk.moSketchRelMgr_c.FUN_4c6035c0": (
            NativeField("Embed", "f78", "rf.suObList"),
            NativeField("Embed", "f40", "sk.EquationVarValueMap_c.FUN_4c339ca0"),
        ),
        "sk.pnt3DcoincMap_c.FUN_4b9611e0": (
            NativeField(
                "Array",
                "m0",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate sk.pnt3DcoincMap_c.FUN_4b9611e0 m0"),
                ),
                CountValue="m0_n",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "m1",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate sk.pnt3DcoincMap_c.FUN_4b9611e0 m1"),
                ),
                CountValue="m1_n",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "m2",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate sk.pnt3DcoincMap_c.FUN_4b9611e0 m2"),
                ),
                CountValue="m2_n",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "m3",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate sk.pnt3DcoincMap_c.FUN_4b9611e0 m3"),
                ),
                CountValue="m3_n",
                ModeValue="Positive",
            ),
        ),
        "sk.sg2DEnt.FUN_4c583460": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "vis", "moEntVisProp_c"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "Not",
                    (
                        "bool",
                        (
                            "lookup_or",
                            ("context",),
                            ("literal", "sketch_owner_1ed8"),
                            ("literal", 0),
                        ),
                    ),
                ),
            ),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "dflt", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Scalar", "f30", "u16"),
                    NativeField("Scalar", "f34", "u16"),
                    NativeField("Scalar", "f38", "u16"),
                    NativeField("Embed", "lw", "utLineWidth_c.Serialize2"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    ("lookup_or", ("scope",), ("literal", "dflt"), ("literal", 0)),
                    ("literal", 0),
                ),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sg2DEnt.FUN_4c583460 Branch"),
                ),
                OtherValue=(NativeField("Node", "ext", "sgExtEnt_c"),),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        (
                            "lookup_or",
                            ("context",),
                            ("literal", "conditions"),
                            ("literal", 0),
                        ),
                        ("literal", 2),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Scalar", "f54", "u16"),
                    NativeField("Scalar", "f56", "u16"),
                ),
                OtherValue=(
                    NativeField("Fail", "alternate sk.sg2DEnt.FUN_4c583460 Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    ("lookup_or", ("scope",), ("literal", "dflt"), ("literal", 0)),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "f50", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(NativeField("Node", "group", "moGroup"),),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "compare",
                            ("Eq",),
                            (
                                "lookup_or",
                                ("scope",),
                                ("literal", "dflt"),
                                ("literal", 0),
                            ),
                            ("literal", 0),
                        ),
                    ),
                    NativeField("Scalar", "has_name", "u8"),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField(
                                "Fail", "alternate sk.sg2DEnt.FUN_4c583460 Branch"
                            ),
                        ),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "compare",
                            ("NotEq",),
                            ("lookup", ("scope",), ("literal", "has_name")),
                            ("literal", 0),
                        ),
                    ),
                    NativeField("Scalar", "f68", "f64"),
                    NativeField("Scalar", "f74", "u32"),
                    NativeField("Scalar", "f78", "u32"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        ("lookup_or", ("scope",), ("literal", "f54"), ("literal", 0)),
                        ("literal", 3),
                    ),
                    ("literal", 3),
                ),
            ),
        ),
        "sk.sgBlockManager.FUN_4c90b810": (
            NativeField(
                "Array",
                "blocks",
                "i32",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgBlockManager.FUN_4c90b810 blocks"
                    ),
                ),
                CountValue="n",
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "map",
                "i32",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgBlockManager.FUN_4c90b810 map"),
                ),
                CountValue="m",
                ModeValue="Positive",
            ),
            NativeField("Embed", "f40", "sk.sgEntHandleDataManager_c.FUN_4c90bf80"),
        ),
        "sk.sgCreationIDs.FUN_4c5864f0": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f10", "i32"),
            NativeField("Scalar", "f14", "i32"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f1c", "i32"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f24", "i32"),
            NativeField("Scalar", "f28", "i32"),
            NativeField("Scalar", "f2c", "i32"),
            NativeField("Scalar", "f30", "i32"),
            NativeField("Scalar", "f34", "i32"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f40", "i32"),
            NativeField("Scalar", "f3c", "i32"),
        ),
        "sk.sgDim.FUN_4c5868d0": (
            NativeField("Base", "Dimension_c.Serialize"),
            NativeField("Scalar", "f80", "i32"),
            NativeField("Scalar", "f90", "u16"),
            NativeField("Scalar", "f94", "u16"),
            NativeField("Scalar", "f98", "u16"),
        ),
        "sk.sgEntHandle.Serialize": (
            NativeField("Scalar", "idx", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgEntHandle.Serialize Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    ("lookup", ("scope",), ("literal", "idx")),
                    ("literal", 30591),
                ),
            ),
            NativeField("Scalar", "f1c", "i32"),
            NativeField("Scalar", "f08", "i32"),
        ),
        "sk.sgEntHandleDataManager_c.FUN_4c90bf80": (
            NativeField(
                "Array",
                "items",
                "i32",
                BodyValue=(
                    NativeField(
                        "Fail",
                        "alternate sk.sgEntHandleDataManager_c.FUN_4c90bf80 items",
                    ),
                ),
                CountValue="n",
                ModeValue="Positive",
            ),
        ),
        "sk.sgLine.FUN_4c58ac90": (
            NativeField("Base", "sk.sgSegment.FUN_4c590920"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgLine.FUN_4c58ac90 Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        ("lookup_or", ("scope",), ("literal", "f56"), ("literal", 0)),
                        ("literal", 512),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "fe8", "u16"),
        ),
        "sk.sgLogDim.Serialize": (
            NativeField("Base", "sk.sgDim.FUN_4c5868d0"),
            NativeField("Scalar", "fa0", "u16"),
            NativeField("Scalar", "fa4", "u16"),
        ),
        "sk.sgLogG1Dim.Serialize": (
            NativeField("Base", "sk.sgLogDim.Serialize"),
            NativeField("Node", "h1", "sgEntHandle"),
        ),
        "sk.sgLoopManager.FUN_4c58cf30": (
            NativeField(
                "Array",
                "loops",
                "i32",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgLoopManager.FUN_4c58cf30 loops"
                    ),
                ),
                CountValue="n",
                ModeValue="Positive",
            ),
        ),
        "sk.sgPoint.FUN_4c58f910": (
            NativeField("Base", "sk.sg2DEnt.FUN_4c583460"),
            NativeField("Scalar", "pflags", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Embed", "pos", "mgPoint_c.restore2D"),),
                OtherValue=(
                    NativeField("Fail", "alternate sk.sgPoint.FUN_4c58f910 Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    (
                        "BitAnd",
                        ("lookup", ("scope",), ("literal", "pflags")),
                        ("literal", 16),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "fe4", "u16"),
            NativeField("Scalar", "fe8", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Node", "h1", "sgEntHandle"),
                    NativeField("Node", "h2", "sgEntHandle"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "BitAnd",
                        ("lookup", ("scope",), ("literal", "pflags")),
                        ("literal", 32),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "fec", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Scalar", "f108", "i32"),
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField("Embed", "p1", "mgPoint_c.restore2D"),
                            NativeField("Embed", "p2", "mgPoint_c.restore2D"),
                        ),
                        OtherValue=(
                            NativeField(
                                "Fail", "alternate sk.sgPoint.FUN_4c58f910 Branch"
                            ),
                        ),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "compare",
                            ("NotEq",),
                            (
                                "BitAnd",
                                ("lookup", ("scope",), ("literal", "pflags")),
                                ("literal", 16),
                            ),
                            ("literal", 0),
                        ),
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "BitAnd",
                        ("lookup", ("scope",), ("literal", "pflags")),
                        ("literal", 32),
                    ),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "has_jet", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgPoint.FUN_4c58f910 Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_jet")),
                    ("literal", 0),
                ),
            ),
            NativeField("Scalar", "ff0", "u16"),
        ),
        "sk.sgSegment.FUN_4c590920": (
            NativeField("Base", "sk.sg2DEnt.FUN_4c583460"),
            NativeField("Scalar", "fc8_s", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSegment.FUN_4c590920 Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "lookup",
                        ("scope",),
                        ("Add", ("literal", "fc8"), ("literal", "_s")),
                    ),
                    ("literal", 65535),
                ),
            ),
            NativeField("Scalar", "fcc_s", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSegment.FUN_4c590920 Branch"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("Eq",),
                    (
                        "lookup",
                        ("scope",),
                        ("Add", ("literal", "fcc"), ("literal", "_s")),
                    ),
                    ("literal", 65535),
                ),
            ),
            NativeField("Scalar", "fd0", "u16"),
            NativeField("Scalar", "fd4", "u16"),
            NativeField("Scalar", "seg_tol", "f64"),
        ),
        "sk.sgSketch.FUN_4c5a0f00": (
            NativeField(
                "Array",
                "val_g1",
                "u16",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSketch.FUN_4c5a0f00 val_g1"),
                ),
                CountValue="ng1",
            ),
            NativeField(
                "Array",
                "val_g2",
                "u16",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "part_relations",
                        BodyValue=(NativeField("Node", "d", "sgPntPntDist"),),
                        OtherValue=(
                            NativeField(
                                "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 val_g2"
                            ),
                        ),
                        ModeValue="Context",
                    ),
                ),
                CountValue="ng2",
            ),
            NativeField(
                "Array",
                "val_g3",
                "u16",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSketch.FUN_4c5a0f00 val_g3"),
                ),
                CountValue="ng3",
            ),
            NativeField(
                "Array",
                "offset_dims",
                "u16",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 offset_dims"
                    ),
                ),
                CountValue="noffset",
            ),
            NativeField(
                "Array",
                "log_g1",
                "u16",
                BodyValue=(NativeField("Embed", "d", "sk.sgLogG1Dim.Serialize"),),
                CountValue="nlog1",
            ),
            NativeField(
                "Array",
                "log_g2",
                "u16",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "part_relations",
                        BodyValue=(
                            NativeField("Embed", "d", "sk.sgLogG2Dim.FUN_4c58b970"),
                        ),
                        OtherValue=(
                            NativeField(
                                "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 log_g2"
                            ),
                        ),
                        ModeValue="Context",
                    ),
                ),
                CountValue="nlog2",
            ),
            NativeField(
                "Array",
                "log_g3",
                "u16",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSketch.FUN_4c5a0f00 log_g3"),
                ),
                CountValue="nlog3",
            ),
            NativeField(
                "Array",
                "iso",
                "u16",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSketch.FUN_4c5a0f00 iso"),
                ),
                CountValue="niso",
            ),
            NativeField(
                "Array",
                "linear_patterns",
                "u16",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 linear_patterns"
                    ),
                ),
                CountValue="nlinpatt",
            ),
            NativeField(
                "Array",
                "linear_patt_cons",
                "u16",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 linear_patt_cons"
                    ),
                ),
                CountValue="nlincon",
            ),
            NativeField(
                "Array",
                "circular_patterns",
                "u16",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 circular_patterns"
                    ),
                ),
                CountValue="ncircpatt",
            ),
            NativeField(
                "Array",
                "circular_patt_cons",
                "u16",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 circular_patt_cons"
                    ),
                ),
                CountValue="ncirccon",
            ),
            NativeField("Node", "f118", "suObList"),
            NativeField(
                "Array",
                "list_7c0",
                "u16",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSketch.FUN_4c5a0f00 list_7c0"),
                ),
                CountValue="n7c0",
            ),
            NativeField(
                "Array",
                "list_9f0",
                "u16",
                BodyValue=(
                    NativeField("Fail", "alternate sk.sgSketch.FUN_4c5a0f00 list_9f0"),
                ),
                CountValue="n9f0",
            ),
            NativeField("Scalar", "ngroup", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Repeat",
                        "groups",
                        BodyValue=(
                            NativeField(
                                "Fail", "alternate sk.sgSketch.FUN_4c5a0f00 groups"
                            ),
                        ),
                        CountValue="ngroup",
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "Not",
                    (
                        "lookup_or",
                        ("context",),
                        ("literal", "DAT_4db92e80"),
                        ("literal", 0),
                    ),
                ),
            ),
        ),
        "sk.sgSlotManager_c.FUN_4c59a5f0": (
            NativeField("Scalar", "f10", "i32"),
            NativeField(
                "Array",
                "slots",
                "i32",
                BodyValue=(
                    NativeField(
                        "Fail", "alternate sk.sgSlotManager_c.FUN_4c59a5f0 slots"
                    ),
                ),
                CountValue="n",
                ModeValue="Positive",
            ),
        ),
    }
)
