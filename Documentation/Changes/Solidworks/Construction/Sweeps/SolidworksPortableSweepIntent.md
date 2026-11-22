# Portable Standard sweep definition

Interchange JSON now retains an explicit path sketch in `SweepFeature` and
checks it against the distinct section sketch on the feature step. The internal
SOLIDWORKS planner resolves those two sketch links, both editable D1 owners and
the sole solid's physical density into the scoped cold Standard swept boss
composer.

The [portable model contract and process evidence](../../../../../re/solidworks/records/SdkPortableSweepDoc2026.md)
describe the permitted circle, quarter arc, constraints and units. Both
disclosed original models reproduce their native-tested files byte for byte.
The verification entry point is the internal SDK planner.
