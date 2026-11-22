# Disclosed F14c part with three generated origin axes

The generated candidate awaits native measurement. Its strict SDK
history reads the three axes and one Body. Its default geometry read
refuses with `SLDPRT contains no readable Parasolid payload`. This is
an experimental step for `B04-SW2026-FCSTD-BOX`, owned by
`/root/assembly_frontier` under PR #121. [Frozen host evidence](../measurements/2026/AttachedBoxAxesCandidate01.json)

## Shared authority

Aggregate `2c151bc84a2444d0b164e087ef80f577c0eacb12` has one measured
reference-axis constructor. It covers the Top-first, Right-second
negative Z hinge of the oblique pattern. It uses `moRefAxis_c` and
`moPlaneInterAxisData_c`. Its display helper requires a nonnegative
world box and its wrapper helper assumes an embedded plane matrix.
The attached F14c box has a negative Y extent. Its X and Y axes also
require Front, whose default transform uses `has_matrix=0`.
[Existing finite hinge](LocalLinearPatternHingeAxisGraph2026.md)

The pinned native routine preserves `f80/f88` order, derives the
direction from the cross product of the two actual normals and clips
the line to the first selected plane's finite display rectangle. The
native default-plane routines derive the center and half-span from
the model box. Disclosed native Z-axis endpoints and actual principal
displays confirmed these operations. The earlier oblique author also
observed non-null X and Y axes and their two-parent dependencies. That
batch failed later and supplies no alternate-axis saved wire evidence.
[Native calls and finite extent](LocalLinearPatternFiniteHinge2026.md)
[Disclosed sign observations](FreecadObliqueCylinderSign2026.md#preserved-disclosed-failure)

## Generated ownership

The intake verifies the intact FCStd source and passes only clean
typed model data to the guarded worker. The signed rectangular stock
supplies world bounds `(0, -10, 0)` to `(20, 0, 30)` mm. The actual
principal plane frames supply the projected display centers and four
ordered borders. Each half-span uses `span * 0.5 + span * 0.05`. The
first selected rectangle determines the stations of its contained
intersection. [Source axes](FreecadAttachedOriginAxes2026.md)

| Axis | Allocated ID | Ordered planes | Matrix flags | Proposed stations (mm) |
| --- | ---: | --- | --- | --- |
| `X-axis` | 27 | Top, Front | 1, 0 | −1 to 21 |
| `Y-axis` | 28 | Front, Right | 0, 1 | −10.5 to 0.5 |
| `Z-axis` | 29 | Right, Top | 1, 1 | −1.5 to 31.5 |

The source origin and all three source axes must have model visibility
true. A hidden or differently ordered input refuses. The ordinary
feature initializer supplies the generated `hidden=0` wire field.
Viewport visibility and source GUI extents remain unqualified. Each
plane wrapper owns an independent local reference, its actual datum
and the matching creation stamp in both headers. Front preserves its
typed default transform without a matrix. Native acceptance of the
Front branch and combined XYZ display remains to be measured.

The stock builder's original allocator registers the three axis rows
after the existing box features and retains source axis role order.
Both headers append real creation logs and publish frontier 30. The
keywords use the ordinary `Axis` tag. Independent readback matches all
19 prior root identities and the stock atom named `Body` and finds 22
total roots. The typed Config and Resolved pair replays exactly at
map `90 → 269`. Grouping under a FreeCAD-style Origin remains open.

The new container is 10,707 bytes with SHA-256
`0d4cba0b66e443e487793204dc82985d5206704a0646b63afb1a4c410b1c54cc`.
At a common locator the axis delta changes CMgr, Config-0-ModelHeader,
Config-0-ResolvedFeatures, Header2 and KeyWords. The other seven
streams are byte-identical. At its earlier locator, the no-axis arm
reproduces the native-measured 10,189-byte archive and all 12 stream
digests. Two fresh stdin workers record zero runtime input reads.
Two independent staging directories reproduce the same packet.

## Reproduce and measure

Use the hash-verified CADMPEG F14c original and an unused directory.
The packet contains `Build.json` and the generated `F14c.SLDPRT`.

```sh
python3.14 -I -B re/tooling/sw2026/attached_top_box_source/PrepareAttachedAxisTrial.py stage \
  /path/to/recipe-0.21.2-F14c.FCStd /tmp/AttachedBoxAxesCandidate01
python3.14 -I -B re/tooling/sw2026/attached_top_box_source/PrepareAttachedAxisTrial.py verify \
  /tmp/AttachedBoxAxesCandidate01 93189f21691fc1cd3ba0f26beb62541f85ac3f814ae68444d178f639099efe60
```

Use the fresh encoded locator `C:\KitAttachedBoxAxes01\F14c.SLDPRT`.
Measure the disclosed control in separate sessions before and after
the candidate lifecycle. Extend the existing signed Top observer
with all three named `RefAxis` features, their two actual parents,
`IRefAxis.GetRefAxisParams` and the model and viewport visibility
observations. Keep the ordinary zero-error and zero-warning checks,
full tree, three live edit branches, actual dimensions, signed solid
and source properties. Preserve each derivative for a fresh reopen.
The manifest gives independent geometry and range predictions for each
edit. Retain any stationary interval after an edit as evidence of the
native update policy. Check saved `f80/f88` order independently of
the parent enumeration order reported by COM.
[Existing signed Top observer](../../tooling/sw2026/attached_top_box_source/RunAttachedTopBoxSources.py)

This packet adds no native observations, public writer admission,
held-out coverage, or FCStd roster credit.
