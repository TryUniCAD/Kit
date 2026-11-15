from __future__ import annotations

from Dsl import Vgt, Vge, i32, u16, f64, obj, base
from Schema import Op

PLAIN = (
    "moUserUnits_c", "mo2CombinedUnits_c", "moFloatNumberUserUnits_c", "moFrequencyUserUnits_c",
    "moGravityUnits_c", "moLinearMotorUnits_c", "moNumberUserUnits_c", "moPrecFormatFloatNumberUserUnits_c",
    "moRotaryMotorUnits_c", "moSpringConstantUnits_c", "moStressUnits_c",
)
ANGLE = ("moAngleUserUnits_c", "moForceUnits_c", "moUnitSysUnits_c")
ENERGY = ("moEnergyUnits_c", "moPowerUnits_c", "moSpecificHeatUnits_c", "moThermalConductivityUnits_c", "moTimeUnits_c")
LENGTH = ("moLengthUserUnits_c", "moLightIntensityUserUnits_c", "moPercentUserUnits_c")
DENSITY = ("moDensityUnits_c", "moVolumeUserUnits_c")
PERDEG = ("moPerDegreeUnits_c", "moStressCombinedUnits_c")
TABLES = ("moUnitsTable_c", "moSimulationUnitsTable_c")


class HasObj(Op):
    def __init__(self, flag, field):
        self.flag, self.field = flag, field

    def load(self, ar, scope, o):
        v = ar.prim("u8")
        scope[self.flag] = v
        if v != 0:
            scope[self.field] = ar.obj()

    def store(self, ar, scope, o):
        v = getattr(scope, "own", scope).get(self.field)
        ar.prim("u8", 1 if v is not None else 0)
        if v is not None:
            ar.obj(v)


def define(reg):
    reg.define("moUserUnits_c.Serialize", [
        i32("f0c"),
        i32("f10"),
        f64("f18"),
        i32("f20"),
        i32("f24"),
        Vgt(0x822, [f64("f30")]),
        i32("f28"),
        Vgt(0x1AA, [i32("f6c")]),
        Vge(0x306, [i32("f70")]),
        Vgt(0x1041, [i32("f74")]),
        Vge(0x1BD2, [f64("f88"), u16("f7c")]),
        Vgt(0x1BD6, [i32("f08")]),
    ])
    for c in PLAIN:
        reg.define(c, [base("moUserUnits_c.Serialize")])
    for c in ANGLE:
        reg.define(c, [base("moUserUnits_c.Serialize"), u16("fb0")])
    for c in ENERGY:
        reg.define(c, [base("moUserUnits_c.Serialize"), Vgt(0xDCE, [u16("fb0")])])
    for c in LENGTH:
        reg.define(c, [base("moUserUnits_c.Serialize"), u16("fb0"), Vgt(0x926, [obj("fb8")])])
    for c in DENSITY:
        reg.define(c, [
            base("moUserUnits_c.Serialize"),
            Vgt(0x92E, [u16("fc0"), u16("fc4")]),
            Vgt(0xAC6, [
                HasObj("has_fb8", "fb8"),
                Vgt(0x180A, [Vgt(0x1FAA, [u16("fc8"), i32("fcc")])]),
            ]),
        ])
    for c in PERDEG:
        reg.define(c, [base("moUserUnits_c.Serialize")])
    reg.define("moTemperatureUnits_c", [base("moUserUnits_c.Serialize"), u16("fb4")])
    for c in TABLES:
        reg.define(c, [Vge(0x69, [base("su_CObArray")], [base("suObList")])])
