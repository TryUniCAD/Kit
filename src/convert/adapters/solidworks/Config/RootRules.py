from convert.adapters.solidworks.Container.Archive import KLayoutValue


# variable strings preserve the measured leading and trailing fixed widths in each owner
def TextRule(
    SlotValue: str, AtValue: int, TailValue: int = 0
) -> dict[str, KLayoutValue]:
    return {
        "slot": SlotValue,
        "rule": "string",
        "at": AtValue,
        **({"tail": TailValue} if TailValue else {}),
    }


# version and state guards consume fields only when their measured condition holds
def GuardRule(
    SlotValue: str,
    AtValue: int,
    PredAt: int,
    PredWidth: int,
    Expected: int,
    TailValue: int = 0,
) -> dict[str, KLayoutValue]:
    return {
        "slot": SlotValue,
        "rule": "guard",
        "at": AtValue,
        "predicate_at": PredAt,
        "predicate_width": PredWidth,
        "values": [Expected],
        **({"tail": TailValue} if TailValue else {}),
    }


# the part root must bind its first six children before walking later scopes
KRootClasses: dict[str, KLayoutValue] = {
    "moPart_c": {
        "child_slots": [
            "moNodeName_c",
            "moVisualProperties_c",
            "moUnitsTable_c",
            "moUnitComponent_c",
            "gcCurvatureObject_c",
            "moTransRefPlaneData_c",
        ],
        "runs": {"1": 0, "2": 0, "4": 0},
        "variable_runs": [
            GuardRule("lead", 0, 8, 4, 19000, 12),
            GuardRule("0", 0, 4, 4, 1073741824),
            TextRule("0", 16, 4),
            GuardRule("3", 4, 0, 4, 0),
            GuardRule("3", 4, 0, 4, 0),
            GuardRule("3", 1, 0, 1, 0),
        ],
    },
}

# appearance spans occur in this order before unit children can be resolved
KVisualRules: list[KLayoutValue] = [
    TextRule("leaf", 12),
    TextRule("leaf", 0),
    GuardRule("leaf", 52, 48, 4, 0),
    TextRule("leaf", 20),
    GuardRule("leaf", 8, 4, 4, 1),
    TextRule("leaf", 8),
    TextRule("leaf", 81),
    TextRule("leaf", 12),
    TextRule("leaf", 76),
    TextRule("leaf", 4),
    GuardRule("leaf", 4, 0, 4, 0),
    GuardRule("leaf", 4, 0, 4, 0),
    TextRule("leaf", 0),
    TextRule("leaf", 8),
    GuardRule("leaf", 24, 20, 4, 1),
    TextRule("leaf", 192),
    TextRule("leaf", 0),
    TextRule("leaf", 0),
    TextRule("leaf", 0),
    TextRule("leaf", 0),
    TextRule("leaf", 4),
    TextRule("leaf", 0),
    TextRule("leaf", 28),
    TextRule("leaf", 0),
    TextRule("leaf", 8),
    TextRule("leaf", 0),
    TextRule("leaf", 0),
]

# names and presentation are distinct class entries in the same root scope
KVisualOwners: dict[str, KLayoutValue] = {
    "moNodeName_c": {"variable_runs": [TextRule("leaf", 0)]},
    "moVisualProperties_c": {"variable_runs": KVisualRules},
}

# ordinary scalar unit classes consume their own fixed record widths
KUnitLeaves: dict[str, KLayoutValue] = {
    "moNumberUserUnits_c": {"runs": {"leaf": 62}},
    "moFloatNumberUserUnits_c": {"runs": {"leaf": 62}},
    "moSpringConstantUnits_c": {"runs": {"leaf": 62}},
    "moStressUnits_c": {"runs": {"leaf": 62}},
    "moGravityUnits_c": {"runs": {"leaf": 62}},
    "moLinearMotorUnits_c": {"runs": {"leaf": 62}},
    "moRotaryMotorUnits_c": {"runs": {"leaf": 62}},
    "moFrequencyUserUnits_c": {"runs": {"leaf": 62}},
    "moAngleUserUnits_c": {"runs": {"leaf": 64}},
    "moUnitSysUnits_c": {"runs": {"leaf": 64}},
    "moForceUnits_c": {"runs": {"leaf": 64}},
    "moPowerUnits_c": {"runs": {"leaf": 64}},
    "moEnergyUnits_c": {"runs": {"leaf": 64}},
    "moTimeUnits_c": {"runs": {"leaf": 64}},
}

# the remaining root children retain their repeat counts and distinct fixed or guarded widths
KUnitRules: dict[str, KLayoutValue] = {
    "moUnitsTable_c": {
        "child_slots": ["*", "..."],
        "runs": {"lead": 2, "0": 0},
        "repeat_count": {"run": "lead", "width": 2, "at": 0},
    },
    "moLengthUserUnits_c": {
        "child_slots": ["moLengthUserUnits_c"],
        "runs": {"lead": 64, "0": 0},
    },
    "moDensityUnits_c": {"variable_runs": [GuardRule("leaf", 73, 66, 1, 0)]},
    "moUnitComponent_c": {
        "child_slots": ["moPart_c"],
        "runs": {"lead": 0},
        "variable_runs": [GuardRule("0", 1, 0, 1, 0)],
    },
    "gcCurvatureObject_c": {"runs": {"leaf": 48}},
    "moTransRefPlaneData_c": {"runs": {"leaf": 24}},
}

# early ownership excludes the material and atom classes until their stream slots are reached
KPrefixRules = KRootClasses | KVisualOwners | KUnitLeaves | KUnitRules

# the independent material continuation only exposes its own registered children
KMaterialRules: dict[str, KLayoutValue] = {
    "gcXhatch_c": {"variable_runs": [TextRule("leaf", 0, 40)]},
    "moMaterial_c": {
        "child_slots": ["moDensityParameter_c"],
        "runs": {"lead": 0, "0": 0},
    },
    "moDensityParameter_c": {
        "child_slots": ["moNodeName_c", "moNodeName_c"],
        "runs": {"lead": 0},
        "variable_runs": [TextRule("0", 16), GuardRule("1", 9, 8, 1, 0)],
    },
    "uoModelData_c": {"child_slots": ["uoScene"], "runs": {"lead": 0, "0": 4}},
}

# the later atom scope can resolve the name and visual owners without reopening the layout resource
KAtomRules: dict[str, KLayoutValue] = {
    "moAtom_c": {
        "child_slots": ["moNodeName_c", "moVisualProperties_c"],
        "runs": {"lead": 0, "1": 58},
        "variable_runs": [TextRule("0", 16, 4)],
    },
}
