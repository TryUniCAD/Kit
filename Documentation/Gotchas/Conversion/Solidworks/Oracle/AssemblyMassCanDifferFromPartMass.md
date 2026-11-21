# Assembly mass can differ from isolated part mass

The same one-body part had equal volume and area when measured alone and as
one resolved occurrence. The isolated mass was `0.000008 kg`; the assembly
reported `0.008 kg`. Two occurrences preserved the expected volume and area,
while the assembly mass was `0.016 kg`. All calls requested system units.

The factor of 1,000 is consistent with different effective density defaults.
The material/density owner has not been traced. Retain both mass observations.
For this no-material, repeated-child geometry batch, verify volume, area, body
count, placement and centre of mass, and report absolute mass separately.
Measure explicit material and density cases before claiming mass equivalence.

The [failed source receipt](../../../../../re/solidworks/measurements/2026/AssemblySourceAttempt01.json)
keeps the original comparison failure and passing bracketing controls.
