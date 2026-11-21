# Revolve angle dimensions follow the active end-condition owner

The SOLIDWORKS 2026 revolve constructor can allocate the driving angle
displays through `moRevEndSpec_c` or through the feature's older direct
slots. The modern switch in the pinned SP05.2 build returns true. The
constructor also checks its incoming discriminator before the switch.

When the modern branch applies, the nested specification owns the
display slots and the feature-level slots are null. The authoring
constructor can allocate both displays. After rebuild, the measured
Mid Plane case retains only its total-angle display; the two-blind-end
case retains both. Keep each live display tied to the actual authored
parameter. [Measured wire modes](RevolveWireModeUsesEndSpec.md)

The [constructor trace](../../../../../../re/solidworks/records/OrdinaryRevolvedBoss2026.md)
gives the pinned locations and the separate profile and axis owners.
