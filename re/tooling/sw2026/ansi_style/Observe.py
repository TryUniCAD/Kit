def require(value, message):
    if not value:
        raise ValueError(message)


def ansi_rules(fields):
    require(
        fields["f10"] == 0 and fields["f138"] == 1,
        "actual standard and constructor-owned f138 disagree",
    )
    require(
        fields["f08"] == 0.00635 and fields["f28"] == 0.00254,
        "ANSI root sizes disagree",
    )
    require(
        fields["f34"] == 0 and fields["f20"] & 0x100000 == 0,
        "ANSI root flag operations disagree",
    )
    require(
        fields["f90"]["f10"] == 0.003175 and fields["f90"]["f18"] == 0,
        "ANSI root height disagrees",
    )
    dims = fields["f13b0"]
    require(
        dims["f68"] == 0
        and dims["f20"] == 0.00127
        and dims["f28"] == 0.003175
        and dims["f38"] == 0.0127
        and dims["f64"] == 1,
        "ANSI dimension root disagrees",
    )
    for name, kind in (
        ("fe0", "linear"),
        ("f1f0", "angle"),
        ("f2f8", "arc_length"),
        ("f3f8", "radial"),
        ("f500", "hole"),
        ("f608", "ordinate"),
        ("f718", "angular_ordinate"),
        ("f830", "chamfer"),
        ("f960", "diameter"),
        ("fa68", "base"),
    ):
        value = dims[name]
        require(
            value["f08"] == 0 and value["f84"] == value["f8c"] == 2,
            "ANSI concrete dimension fields disagree",
        )
        require(
            value["f88"] == (2 if kind in ("angle", "angular_ordinate") else 3),
            "ANSI angular predicate disagrees",
        )
        require(
            value["fe0"] & 0x200 != 0
            and bool(value["fe0"] & 0x400) == (name in ("fe0", "f1f0", "f2f8")),
            "ANSI per-operation flag masks disagree",
        )
        require(
            value["fe8"]["f10"] == 0.003175 and value["fe8"]["f18"] == 0,
            "ANSI dimension height disagrees",
        )
    require(
        dims["fe0"]["f100"] == 1
        and dims["fe0"]["f104"] == 0
        and dims["fe0"]["f108"] & 0x30 == 0x20,
        "ANSI linear subtype disagrees",
    )
    require(
        dims["f718"]["f100"] == 0
        and dims["f718"]["f6c"] == 2
        and dims["f830"]["f6c"] == 0,
        "ANSI special dimension subtype disagrees",
    )
    return {
        "native_constructor_sequence_checked": True,
        "native_execution_observed": False,
    }
