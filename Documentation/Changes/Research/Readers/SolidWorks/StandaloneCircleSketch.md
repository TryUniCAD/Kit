<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Standalone SOLIDWORKS circle reader

A04d repairs the public reader for the five original P02 circle archives in
`re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39`. Previously they exposed
one fallback body, duplicated circle geometry, no Origin coincidence and the
Front datum even for the YZ source. The new standalone path requires the complete
typed configuration and resolved history before replacing that compatibility
projection. It reuses the existing circle, driving diameter, ordered coincidence
and principal-datum bindings. [Framing finding](../../../../../re/solidworks/records/CircularSketchOnly.md)

Both public BRep modes, with default and strict options, now return zero bodies,
one physical circle and its fixed construction Origin point, the driving diameter
and ordered coincidence. Radii are 5 mm, or 8 mm for the diameter edit. The inch
source preserves its display unit while physical parameters remain millimetres.
The YZ sketch resolves its actual Right Plane and dependency. Original capture
hashes and sizes are checked before and after reading.

The five sources have independent licensed observations recorded in
[Circle binding readback](../../Workers/SolidWorks/CircleBindingReadback.md).
Zero bodies is correct for these standalone sketch sources. This reader repair
does not establish native output acceptance, lossless translation, P02 pair
qualification or the P05 holdout. Existing unqualified reader metadata and retained
native/cache evidence remain intact.

## Verification

From the changed checkout, set `$PythonExe` to the pinned Python 3.14.6 environment's executable.

```powershell
$env:PYTHONPATH="$PWD/src;$PWD/Cli;$PWD"
$env:PYTHONDONTWRITEBYTECODE='1'
rtk test $PythonExe -m pytest -q -p no:cacheprovider --import-mode=importlib tests/Convert/Solidworks/Core/CircleOnly
```

The focused Windows run passed 51 checks in 71.94 seconds. These cover all five saved sources in
four public option combinations, neutral JSON roundtrip, actual boss/cut
counterexamples, contradictory diameter/support/flags/footer records, an actual
decoded solid partition and extra authored history. Unsupported conversion raises
before replacing an existing destination in default and strict modes. Five fresh
process pairs install audit guards before SDK import, read private source copies,
delete those copies, then reconstruct and validate the serialized neutral model.
The guards forbid CAD imports, dynamic library loads, process/network operations
and repository fixture reads. These are neutral model proofs, not native output
or application acceptance tests.

An additional offline replay used the sealed private cohort
`.rescratch/AutomationA04cRadialDiscovery5093-Attempt01`.
All three `Discovery-D13`, `Discovery-D19` and `Discovery-D23` archives retained one
body, a join, one circle plus Origin, diameter and coincidence, and no diagnostics
in both BRep modes. Every archive matched the original `Attempt.json` SHA-256 and
size before and after replay. No CAD process or save was performed.

Black, Ruff and focused steering verification cover the new parser, projection
and public/process tests. Black stdin uses the repository configuration for Core
paths because the existing `re/` exclusion also matches the suffix of `Core/`.
The integration edit adds only one import and one composition call in Adapter.
