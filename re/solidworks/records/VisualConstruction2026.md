# Generated model visual properties in SOLIDWORKS 2026

Status: generated visual state passes clean native opening. The initial
visual-only revision had no body; the later configuration-progress repair
produced the three solids measured in
[PolygonNativeMeasurements2026.md](PolygonNativeMeasurements2026.md).
Production writing remains disabled. No saved appearance values or payloads are
inputs to this constructor.

## Required ownership

The [controlled initial-update capture](../v2026/evidence/TupniInitialFrame.json)
records an access violation reading address `0xc` from a null visual-properties
source, after a healthy control passes with the same one-hook observer.
The immediate source is model virtual getter slot `+0x1040` at
`0x4c1f46d0`, copied by call `0x4c1f4737` into the current configuration's
missing appearance. Model member `+0xd78` is that base configuration, not another
model.

Part vtable `0x4d1252d8` binds getter slot `+0x1040` to `0x4c027340` and setter
slot `+0x1048` to `0x4c036f40`. The getter uses the display-state service. Its
fallback at `0x327aaaa0` casts a displayed entity to `moConcept_c` and reads
concept member `+0x78` at `0x327aad45`. The setter also stores concept `+0x78`.
The active `moConcept_c` archive schema serializes this object as `f78`.
The native lightweight serializer at `0x4c17a7b0` writes the visual object at
`0x4c17a865` and, on load, reads it at `0x4c17a944` before assigning member
`+0x78` at `0x4c17a971`. These are native load/store ownership boundaries.

The display-state addresses bind to `sldvisualstateu.dll`, base `0x32700000`,
SHA-256 `fb85d7921c52393e8bb847258b72d8cd006b37c118138c8260c6efe7dcc22c2c`.
The model addresses bind to `sldmodu.dll`, base `0x4b140000`, SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

The builder previously used the general concept constructor's absent optional
appearance for the model as well as features. The model now owns a generated
`moVisualProperties_c` record. Origin and ordinary profile optional overrides
remain separately owned. No runtime pointer is written into the archive.

## Constructor and wire authority

The following addresses bind to `sldmfcu.dll`, preferred image base `0x3c720000`,
SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`.

| Record                       | Constructor                   | Wire authority                            |
| ---------------------------- | ----------------------------- | ----------------------------------------- |
| Visual properties            | `0x3c920bb0`                  | `Serialize 0x3c921110`, `save 0x3c922e60` |
| Embedded material properties | `0x3c84e7b0`                  | `save 0x3c851d70`                         |
| Material user properties     | Base constructor `0x3c84e3d0` | `save 0x3c888140`                         |

Runtime-class record `0x3ce70e20` gives visual object size `0xb8` and raw schema
`0x80000001`, hence wire schema 1. Registry loading is alphabetical;
`SmallCMgr.py` replaces the earlier provisional visual schemas. Its explicit
presence keys below are required even for absent optional children.

## Visual field classification

Every value below is a native constructor constant or constructor-derived
absence, independent of a saved document. The material is a fresh owned record.

| Active field | Generated value             | Evidence                                                      |
| ------------ | --------------------------- | ------------------------------------------------------------- |
| `f0c`        | `0xc0c0c0`                  | Literal assignment at `0x3c920bd8`                            |
| `f14`        | `0`                         | Upper 32 bits of constructor qword assignment at `0x3c920bdf` |
| `f18`        | `0xc0c0c0`                  | Literal assignment at `0x3c920be7`                            |
| `f20`        | Fresh material record below | Allocation and constructor call `0x3c920bee`–`0x3c920c10`     |
| `f40`, `f50` | Empty strings               | Default string constructors at `0x3c920c24` and `0x3c920c39`  |
| `f48`        | `0`                         | Constructor `0x3c920c2f`                                      |
| `f4c`        | `1`                         | Constructor `0x3c920c32`                                      |
| `f58`, `f5c` | `0`                         | Zero qword assignment at `0x3c920c44`                         |
| `f78`        | `-1`                        | Constructor `0x3c920c54`                                      |
| `f7c`, `f80` | `0`                         | Zero qword assignment at `0x3c920c5b`                         |
| `has88`      | `0`                         | Constructor-null optional DSPBR pointer at `0x3c920c5f`       |

Wire order is `f0c, f14, f18, f20, f40, f48, f4c, f50, f58, f5c, f78, f7c,
f80, has88`. The visual serializer throws if the mandatory material pointer is
null. Optional texture and shader payloads are not needed for this default
constructor state.

The part's authored constructor at `0x4c19f170` allocates this visual class at
`0x4c19f970`, calls the default constructor at `0x4c19f982`, then calls
`setDefaultAppearance(1)` at `0x4c19f998` before installing it through
`setVizProp` at `0x4c19f9a4`. The setter at `0x3c77b970` stores its argument in
visual member `+0x5c` and notifies visual state. The model factory therefore
sets `f5c=1` after the generic visual constructor. The generic constructor's
zero is not the final model appearance flag.
The notification tail finds constructor-zero members `+0x64` and `+0x70`, so
it changes no other serialized field before installation.

## Material field classification

| Active field                      | Generated value | Evidence                                                                                      |
| --------------------------------- | --------------- | --------------------------------------------------------------------------------------------- |
| `f28`, `f20`, `f30`, `fb8`        | Empty strings   | Default string constructors `0x3c84e7cd`–`0x3c84e7ed`, `0x3c84e86f`                           |
| `f38`, `f40`, `f48`               | `1.0`           | Exact double literal assignment `0x3c84e7ee`–`0x3c84e800`; ambient, diffuse, specular getters |
| `f50`                             | `0.3125`        | Literal bits `0x3fd4000000000000` at `0x3c84e804`; shininess getter                           |
| `f58`, `f60`                      | `0.0`           | Zero assignments at `0x3c84e814` and `0x3c84e818`; transparency and emission getters          |
| `f68`, `f70`, `f74`, `f78`, `f7c` | `1`             | Constructor assignments `0x3c84e81c`–`0x3c84e839`                                             |
| `f6c`                             | `0`             | Upper half of qword assignment at `0x3c84e81c`                                                |
| `has80`, `has90`, `has98`         | `0`             | Constructor-null texture, appearance and texture pointers `0x3c84e840`–`0x3c84e855`           |
| `props.n`, `props.props`          | `0`, empty list | Empty native vector; count formula `(end - begin) >> 4` at `0x3c76af50`                       |

The user-property constructor chain is `0x3c84e3d0 → 0x3c74e1e0 → 0x3c74be70 →
0x3c74c6f0`; it zeros begin, end and capacity. The wire count follows from the
empty collection. No captured count or saved property row is used.

Material wire order is `f28, f20, f38, f40, f48, f50, f58, f60, has80, f68,
f6c, f70, f74, f78, f30, f7c, has90, fb8, has98, props`.

## Verification limits

The complete-file process harness now checks the decoded model's concrete visual
record and distinct profile ownership. Its existing strict construction boundary
denies runtime file reads and process launches; linked stream maps and byte
identity remain required. These checks run only in remote PR CI.

Head `60d01ec0de6937602c10980d6eddf6a43605cf7e` passed remote job
`132812541055`: 149 policy checks, 163 native checks and 158 existing skips.
Artifact `14160779989` binds to synthetic merge
`d35a0b352abece4095b2843ec8c6cb673b2b71d1`, whose parents include that head.
The new H3 candidate is 7,061 bytes, SHA-256
`f3a2169124976ca55524bc83ef6c2f6c5825baea912900b411a9e5bfad8af079`.
All eight modeled stream checks passed, the computed map counter is 71, and
the complete-file ownership and strict runtime access checks passed.

The [clean native measurement](../measurements/2026/FreshPartModelAppearance.json)
opens that exact generated file and completes all fourteen measurement stages
between two healthy original controls, on verified build `34.5.2.0604`.
It reports zero open errors, warnings, rebuild errors and feature errors or
warnings, with no dialogs or cleanup errors. Both locked inputs remain unchanged.

The feature tree contains the named sketch and extrusion with depth `0.013 m`,
but both are suppressed. Body count, volume and area are zero. This closes the
specific null-source opening failure; it does not establish a geometric or
editable generated part. Configuration state and native regeneration remain
unfinished, and generated-output acceptance remains zero.
