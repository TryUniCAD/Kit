# Native quaternion rotation uses a negative half-angle

## Expectation

An axis-angle helper uses the familiar positive half-angle quaternion formula
once its axis, angle and multiplication order have been identified

## Actual behavior

The locked SOLIDWORKS 2026 `sldmgu.dll` has preferred base `0x31dd0000` and
SHA-256 `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c`
Its `mg_RotationQuaternion` helper starts at `0x31f0fa20`
Instruction `0x31f0fa84` multiplies the incoming angle by the binary64 operand
at `0x31f46ff0`, whose value is `-0.5` and bits are `0xbfe0000000000000`
The following cosine and sine calls consume that negative half-angle

The initial construction record assumed a positive factor without reading the
referenced constant
Generated files opened with a solid body, but numerical native orientation
readback differed from two healthy controls
Direct inspection of the operand refuted the positive-half-angle assumption
The axis vectors were positive canonical axes, and Hamilton multiplication
order and matrix row layout were already correct

## Workaround

Port the actual native primitive, including its referenced constants and signs
For normalized axis `n` and angle `a`, this helper uses `h=-0.5*a` and
`q=(n.x*sin(h),n.y*sin(h),n.z*sin(h),cos(h))`
Retain the caller's documented angle values, quaternion product order and
matrix layout
Read a multiplication instruction's data operand before assigning its meaning
from a familiar mathematical convention

Compute view matrices through those recovered helpers
Do not compensate with a fitted transpose, captured matrix coefficients or
per-view sign patches
Verify native numerical orientation between healthy controls after implementing
the helper; a plausible image or a codec round trip does not establish parity

The [standard-view construction record](../../../../../re/solidworks/records/StandardViewsConstruction2026.md#critical-correction-the-native-half-angle-is-negative)
binds the exact constant, native method hashes, refuted assumption and negative
oracle comparison
