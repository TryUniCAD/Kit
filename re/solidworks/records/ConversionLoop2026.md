# FreeCAD to SOLIDWORKS recovery loop

Status: unfinished. The user authorized up to 1,000 fix-and-retry iterations in
the active goal. The large public assembly remains unconverted. The production
SOLIDWORKS adapter remains read-only.

## Fixed target and completion conditions

The target is the unchanged, hash-locked
[GA3D FreeCAD assembly and native part set](PublicAssemblyAcceptance2026.md),
including its assemblies, parts, editable feature history and mates. The source
site, actual FreeCAD screenshot and native source report are linked in PR 121.
The SOLIDWORKS screenshot must show generated target output. Every
[CAD success criterion](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
and the broader goal-objective coverage still applies.

## Iteration rule

1. Run the current conversion or the failing native-writer prerequisite and
   retain its input identity, generator revision, output digest and first error.
2. Explain the error through source or native dataflow. Recover shared format
   rules; never substitute captured rows, payloads, offsets or templates.
3. Implement the fix and run applicable process checks in remote PR CI.
4. Obtain the newly generated output from that exact revision. Inspect it in a
   fresh SOLIDWORKS process between healthy original vendor-saved controls.
5. Record the actual result, including failed controls, warnings, geometry,
   edit/rebuild/save/reopen evidence and the next error. Repeat until the full
   source conversion passes or the user-set iteration limit is reached.

An iteration is a converter repair followed by newly generated output and its
next inspection. Source authoring, parser traces, failed instrumentation setup,
control-only runs, CI polls and review requests are supporting steps; they are
not extra successful conversions. Invalid controls invalidate acceptance and
must remain recorded. Remote codec passes do not count as native acceptance.

## Current iteration

Iteration 1 is active on the part-writer prerequisite. The current research
candidate comes from independent neutral polygon inputs, not the large public
FreeCAD file. No complete public-project conversion is claimed.

The schema-zero correction is confirmed at the live journal comparison. The
next candidate, SHA-256
`edd138ebf4b9067ce106e947f4c1db988f49366eb697a8aa315af6df806f3b55`,
reaches the part root and throws archive cause five. A selected native trace
shows its first section length being consumed as object-reference index 1883
against read-map length three. The next question is the archive-context file
version and modern/legacy serializer branch, before changing framing or map
arithmetic. [Tupni usage](Tupni2026.md) retains the capture evidence and limits.

The original healthy-control identity is
`c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`.
The separate privacy-redacted parser fixture has digest
`55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6`.
It must not replace the original control in oracle jobs. Earlier failed-control
authoring captures created no training case and supply no solver rule.
