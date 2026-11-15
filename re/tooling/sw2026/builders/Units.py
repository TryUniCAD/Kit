from __future__ import annotations

from collections.abc import Mapping, Sequence

from Core import Obj


CLASS_NAMES = {
    "length": "moLengthUserUnits_c",
    "angle": "moAngleUserUnits_c",
    "number": "moNumberUserUnits_c",
    "density": "moDensityUnits_c",
    "float_number": "moFloatNumberUserUnits_c",
    "spring_constant": "moSpringConstantUnits_c",
    "unit_system": "moUnitSysUnits_c",
    "force": "moForceUnits_c",
    "stress": "moStressUnits_c",
    "gravity": "moGravityUnits_c",
    "linear_motor": "moLinearMotorUnits_c",
    "rotary_motor": "moRotaryMotorUnits_c",
    "power": "moPowerUnits_c",
    "energy": "moEnergyUnits_c",
    "time": "moTimeUnits_c",
    "frequency": "moFrequencyUserUnits_c",
}
CODE_DOMAINS = {
    "length": frozenset(range(11)),
    "angle": frozenset(range(4)),
    "unit_system": frozenset(range(5)),
    "force": frozenset(range(8)),
    "power": frozenset((0,)),
    "energy": frozenset((0,)),
    "time": frozenset(range(6)),
}
LENGTH_CODES = {"mm": 0, "cm": 1, "m": 2, "in": 3, "ft": 4, "angstrom": 6, "nm": 7, "um": 8, "mil": 9, "microinch": 10}
ANGLE_CODES = {"degree": 0, "arcminute": 1, "arcsecond": 2, "radian": 3}
SYSTEM_CODES = {"cgs": 0, "mks": 1, "ips": 2, "mmgs": 4}


def integer(value, name, low=0, high=0x7FFFFFFF):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def base_format(*, decimal_places):
    return {
        "f08": 0,
        "f0c": integer(decimal_places, "decimal places", high=16),
        "f10": 1,
        "f18": 0.01,
        "f20": 10,
        "f24": 1,
        "f28": 1,
        "f30": 0.78539816339745,
        "f6c": 0,
        "f70": 1,
        "f74": 1,
        "f7c": 0,
        "f88": 0.0,
    }


def unit_record(*, kind, unit_code, decimal_places):
    if kind not in CLASS_NAMES:
        raise ValueError(f"unsupported user-unit kind {kind!r}")
    f = base_format(decimal_places=decimal_places)
    if kind in CODE_DOMAINS:
        unit_code = integer(unit_code, f"{kind} unit code", high=0xFFFF)
        if unit_code not in CODE_DOMAINS[kind]:
            raise ValueError(f"the native construction domain for {kind} unit code {unit_code} has not been recovered")
        f["fb0"] = unit_code
    elif unit_code is not None:
        raise ValueError(f"{kind} has no independent serialized unit code")
    if kind == "length":
        f["fb8"] = None
    if kind == "density":
        f.update({"fc0": 3, "fc4": 1, "has_fb8": 0, "fb8": None, "fc8": 3, "fcc": 1})
    return Obj(CLASS_NAMES[kind], f)


def units_table(*, definitions):
    if not isinstance(definitions, Sequence) or isinstance(definitions, (str, bytes, bytearray)):
        raise ValueError("unit definitions must be an authored semantic sequence")
    records = []
    seen = set()
    for definition in definitions:
        if not isinstance(definition, Mapping) or set(definition) != {"kind", "unit_code", "decimal_places"}:
            raise ValueError("each unit definition requires kind, unit_code and decimal_places")
        kind = definition["kind"]
        if not isinstance(kind, str) or kind in seen:
            raise ValueError("a unit table must contain each requested semantic kind once")
        seen.add(kind)
        records.append(unit_record(**definition))
    return Obj("moUnitsTable_c", {"n": len(records), "items": [{"o": record} for record in records]})


def unit_table_profile(*, length_unit, angle_unit, unit_system, decimal_places):
    for value, choices, name in ((length_unit, LENGTH_CODES, "length"), (angle_unit, ANGLE_CODES, "angle"), (unit_system, SYSTEM_CODES, "system")):
        if not isinstance(value, str) or value not in choices:
            raise ValueError(f"unsupported semantic {name} unit {value!r}")
    requested = {
        "length": LENGTH_CODES[length_unit], "angle": ANGLE_CODES[angle_unit],
        "unit_system": SYSTEM_CODES[unit_system], "force": 2,
        "power": 0, "energy": 0, "time": 0,
    }
    definitions = [{"kind": kind, "unit_code": requested.get(kind), "decimal_places": decimal_places} for kind in CLASS_NAMES]
    return units_table(definitions=definitions)
