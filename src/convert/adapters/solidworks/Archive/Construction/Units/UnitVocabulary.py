# native factory order and concrete class identities must remain independent of saved unit tables
KUnitClasses = {
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

# only statically recovered unit code domains may enter fresh native records
KUnitDomains = {
    "length": frozenset(range(11)),
    "angle": frozenset(range(4)),
    "unit_system": frozenset(range(5)),
    "force": frozenset(range(8)),
    "power": frozenset((0,)),
    "energy": frozenset((0,)),
    "time": frozenset(range(6)),
}

# named conversion vocabulary follows the native abbreviation initializer without api enum assumptions
KLengthCodes = {
    "mm": 0,
    "cm": 1,
    "m": 2,
    "in": 3,
    "ft": 4,
    "angstrom": 6,
    "nm": 7,
    "um": 8,
    "mil": 9,
    "microinch": 10,
}

# explicit angular names avoid borrowing application preference state during synthesis
KAngleCodes = {"degree": 0, "arcminute": 1, "arcsecond": 2, "radian": 3}

# document system names follow the preset map and the native custom preference binding
KSystemCodes = {"cgs": 0, "mks": 1, "ips": 2, "custom": 3, "mmgs": 4}

# explicit custom mass choices use their verified density codes independently of the api enumeration
KMassCodes = {"g": 1, "kg": 2}
