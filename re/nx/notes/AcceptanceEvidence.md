# Siemens NX acceptance evidence

## Environment

NX 2506 was installed in the local Windows 11 Parallels VM. The oracle is NX
Open through `run_journal.exe`. The Windows guest reads the host worktree
through `C:\Mac\Home`.

The control is `block.prt`, a controlled NX 2506 part with one block feature
and six expressions. The Kit rewrite is produced by the production adapter and
written with `roundtrip_final.prt`.

## Control output

```text
STATUS 0
PART C:\Mac\Home\Documents\UniCAD\Kit\re\nx\oracle\block.prt
UNITS 1
BODIES 1
BODY 38459 True
FEATURES 2
FEATURE 38784 DATUM_CSYS False
FEATURE 38785 BLOCK False
EXPRESSIONS 6
EXPRESSION p0 40.0
EXPRESSION p1 30.0
EXPRESSION p2 20.0
EXPRESSION height 20.0
EXPRESSION length 40.0
EXPRESSION width 30.0
VOLUME 23999.999999999996
AREA 5200.0
CENTROID [X=19.999999999999996,Y=15,Z=9.9999999999999982]
MASS 0.18793536
```

## Kit rewrite output

The rewrite changes the native `NX_ReferenceSet` attribute from `Empty` to
`KitNX`. NX reports the same body, feature tree, expressions, volume, area,
centroid, and mass.

```text
STATUS 0
PART C:\Mac\Home\Documents\UniCAD\Kit\re\nx\oracle\roundtrip_final.prt
UNITS 1
BODIES 1
BODY 38459 True
FEATURES 2
FEATURE 38784 DATUM_CSYS False
FEATURE 38785 BLOCK False
EXPRESSIONS 6
EXPRESSION p0 40.0
EXPRESSION p1 30.0
EXPRESSION p2 20.0
EXPRESSION height 20.0
EXPRESSION length 40.0
EXPRESSION width 30.0
VOLUME 23999.999999999996
AREA 5200.0
CENTROID [X=19.999999999999996,Y=15,Z=9.9999999999999982]
MASS 0.18793536
```

The native attribute readback is:

```text
STATUS 0
ATTR NX_ReferenceSet KitNX
ATTR NX_ComponentGroup AllComponents
```

## Live rebuild

After the rewrite loaded, NX changed the `length` expression from `40` to `45`
and updated the part:

```text
STATUS 0
BEFORE 40.0
AFTER 45.0
BODIES 1
VOLUME 27000.0
AREA 5699.999999999999
CENTROID [X=22.500000000000004,Y=15.000000000000002,Z=10.000000000000002]
```

## Header changing rewrite

The production adapter wrote `adapter_header_edit.prt` by replacing
`/Root/FastLoad/ExternalReferences` with a value four bytes longer. The rebuild
shifted every later payload offset and recomputed the header seal and footer
fingerprint. NX reported the same body, features, expressions, volume, area,
centroid, and mass as the control:

```text
STATUS 0
PART C:\Mac\Home\Documents\UniCAD\Kit\re\nx\oracle\adapter_header_edit.prt
UNITS 1
BODIES 1
BODY 38459 True
FEATURES 2
FEATURE 38784 DATUM_CSYS False
FEATURE 38785 BLOCK False
EXPRESSIONS 6
EXPRESSION p0 40.0
EXPRESSION p1 30.0
EXPRESSION p2 20.0
EXPRESSION height 20.0
EXPRESSION length 40.0
EXPRESSION width 30.0
VOLUME 23999.999999999996
AREA 5200.0
CENTROID [X=19.999999999999996,Y=15,Z=9.9999999999999982]
MASS 0.18793536
```

The seal formula was confirmed on seven NX saved variants, including two
directory layouts, before the writer produced the file.

## Container behavior

The production parser also reads the compound-file corpus:

```text
vise_screw.prt confidence=1.0 container=compound streams=6 feature_steps=1
flange.prt confidence=1.0 container=compound streams=17 feature_steps=1
```

Compound parts do not project B-rep bodies. Modern SPLMSSTR parts do project
the embedded Parasolid B-rep.

## Donor boundary

The production adapter contains no vendor part, no encoded vendor stream, and
no package data. It constructs the root UUID, directory framing, section
index, and stream wrappers from declared format facts. Native payload bytes
come only from the source document during a same-document rewrite.

The synthetic integration test builds its container from code and does not
ship a vendor `.prt` fixture.

## Current head re-verification

The production adapter was re-run on the control at the current head and the
result was opened in a fresh NX 2506 process. The rewrite changes
`NX_ReferenceSet` from `Empty` to `KitNX` and rebuilds the container.

```text
STATUS 0
PART C:\Mac\Home\Documents\UniCAD\Kit\re\nx\oracle\kit_head_check.prt
UNITS 1
BODIES 1
BODY 38459 True
FEATURES 2
FEATURE 38784 DATUM_CSYS False
FEATURE 38785 BLOCK False
EXPRESSIONS 6
EXPRESSION p0 40.0
EXPRESSION p1 30.0
EXPRESSION p2 20.0
EXPRESSION height 20.0
EXPRESSION length 40.0
EXPRESSION width 30.0
VOLUME 23999.999999999996
AREA 5200.0
CENTROID [X=19.999999999999996,Y=15,Z=9.9999999999999982]
MASS 0.18793536
```

The body, feature tree, expressions, volume, area, centroid, and mass match the
control exactly, so the current writer is still vendor loadable and application
usable.

## Class table authoring

The modern type registry is now written as well as read. `WriteRegistry`
reproduces the class table byte for byte on five parts:

```text
wave_modern.prt   8072 bytes  identical
flange_modern.prt 12539 bytes identical
fresh_block.prt   7822 bytes  identical
empty.prt         6399 bytes  identical
dim40.prt         7822 bytes  identical
```

The two per-class fields are derivable: the first is the class's registration id
plus one, and the second is the parent ordinal. The class table is therefore no
longer carried from the source document.

## Head record authoring

The root head record is now emitted for both identity shapes. `HeadParts` splits
the source record at the suffix, `HeadRecord` accepts six or seven identity bytes,
and `HeadSuffix(NextId)` rebuilds the nineteen byte suffix from the next object id:

```text
HeadSuffix(214) == empty.prt suffix        True
HeadSuffix(251) == const_box60.prt suffix  True
HeadRecord(source text) == source head     empty, const_box60, dim40, multi, sweep
```

Writing through the adapter and opening in NX 2506:

```text
const_box61.prt  STATUS 0  BODIES 1  FEATURES 1  EXPRESSIONS 3
                 VOLUME 36000.0  AREA 7199.999999999999  MASS 0.28190304
headtest/empty.prt  STATUS 0  BODIES 0  FEATURES 0  EXPRESSIONS 0
headtest/dim40.prt  STATUS 0  BODIES 1  FEATURES 1  EXPRESSIONS 3
                 VOLUME 23999.999999999996  AREA 5200.0  MASS 0.18793536
```

The body, feature tree, expressions, volume, area, centroid, and mass match the
controls, so the head record is re-emitted rather than carried for both a
body-less part and a part with a body.
