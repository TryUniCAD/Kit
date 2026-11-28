# FreeCAD F14a fixed origin point

The disclosed FreeCAD 1.1.4 origin box supplies one independently owned `App::Point`, `Origin001`, with native ID 4920. The strict F14a planner now returns its name, coordinates, model visibility and identity beside the line datums. The FreeCAD 1.0.2 contrast has only the six line and plane children. The shared stock and axis constructor produces the same complete containers for both originals. [Guarded point receipt](../measurements/2026/SdkFreecadOriginPoint01.json) · [Axis and stock evidence](FreecadOriginBoxAxes2026.md)

Task `B04-SW2026-FCSTD-BOX/F14a-origin-point`, owner `/root/release_path`, delivery PR #121. The source owner and isolated archive record are verified. Full target placement, selectable identity and native lifecycle remain open. The source geometry and carrier are bound through the existing F14a archive and shape owners. The public write path remains closed.

## Source ownership

The source Body links to the actual `Origin` object (ID 4913). Its ordered `OriginFeatures` list contains the six ordinary planes and lines, then the separate ID 4920 point. `PlanOriginBox` checks that the strict SDK object table exactly matches the retained in-memory archive. `ReadBoxDatums` parses the point's own role, label, visibility and two agreeing stored forms of its unit placement. The position is `(0, 0, 0)` mm and its model visibility is true. The archive has no saved GUI document. Decimal ID 4920 identifies the source object only. The target allocator chooses the next ordinary feature ID.

## Target archive rule

The exact SOLIDWORKS 2026 SP05.2 `sldmodu.dll` is bound by SHA-256 and preferred-image addresses in the receipt. The fixed-coordinate constructor at `0x4c2f7bb0` takes an actual part owner and coordinate and initializes the inherited `moRefGeom_c` position `f6c0`. The named geometry getter follows this same field. The fixed `moRefPointData_c` next to it has no modern schema-one body fields, and the rebuild getter's data callback leaves the stored point in place. The two-axis intersection data class has two wrapper references and its own mode. The lightweight coordinate subclass has a different data body.

| Ordinary schema-one field | Proven owner or formula |
| --- | --- |
| `moRefGeom_c.f6c0` | Actual point coordinates, converted component-by-component from millimeters to meters |
| `f6dc`, `f6e0`, `f6e8`, `f6f0` | Inherited initializer sets 4, 0, null and 0 |
| `moRefPoint_c.f700` | Concrete `moRefPointData_c` object, created with its owning point |
| `f6f8` and `f708` | Fixed constructor sets both nullable profile and surface pointers to null |
| Point data backlink | Modern load restores the runtime pointer after reading the data object |
| Four inherited virtual dispatches | Point and measured axis vtables name the same functions at slots `0x3e8`, `0x3f8`, `0x4b8` and `0x4c0` |
| Ordinary database tail | The serializer's database capability check leaves this branch inactive for the modeled ordinary archive context |

The point constructor and serializer are classified here by read-only exact-build PE exports, schema descriptors, callback identity and independently disassembled control flow. The Hopper bridge timed out before returning an evidence record. The explicit static pins in the receipt are reproducible without shipping the library, its listings or archive content.

## Guarded comparisons

The isolated research record uses the shared typed graph codec and actual generated ordinary stock snapshot. The label and coordinate triple vary with the point intent. The common fields follow the part context and allocator. The constructor checks the allocator handoff and the actual part owner. Ordinary Resolved roots acquire ownership from the enclosing part. No standalone owner pointer is carried in the point record, so the research reader verifies the ordinary single-part context and binds it on decode.

| Input | Output | Result |
| --- | --- | --- |
| Actual FreeCAD 1.1.4 `Origin001` | 351-byte typed record | Live stock next ID 30, five added archive-map slots, byte-exact decode and regeneration |
| Independently authored named point at `(-12.5, 28, 7.75)` mm on the 1.0.2 stock | 363-byte typed record | Same class order and exact `(-0.0125, 0.028, 0.00775)` m, with no authored point attributed to that source |

Two fresh processes per input agree. Each process checks the immutable original, neutral JSON equivalence and the previous complete stock archive. Both research records advance map counter 270 to 275. The source checks refuse an unbound label, foreign source kind, moved point and hidden point. The typed record checks refuse a foreign part owner, reused persistent ID, absent data owner, changed inherited mode, truncation, appended bytes and nonfinite coordinate input. Both normal public writer paths and the in-memory writer stay closed. Model work records zero file reads, CAD launches or network access.

The earlier six-process F14a and F14c comparison still matches every recorded per-case report, including the eleven-kilobyte forward boxes and the native-measured signed Top control. The separate four-process C130 check still emits the exact 9,080-byte named equation model, with its original body name and independent dormant D2. [F14c control](../measurements/2026/SdkFreecadOriginBoxAxes01.json) · [C130 control and rerun](SdkC130SourceOwners2026.md#reproduction)

## Reproduction and remaining native evidence

The input manifest must have SHA-256 `e2053d84764ed9b65fc4bfe62f98b08c4d33bb57f096f3a4e9265e802e9288fa`. Supply the exact licensed library using a path outside the repository. Its SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

```sh
python3.14 -I -B re/tooling/sw2026/f14a_lineage/ProveOriginPoint.py /path/to/FreecadOriginBoxSchema01/Inputs.json /private/path/to/sldmodu.dll
```

The next native control is a fresh ordinary part with a reference point and independently authored coordinates. The documented 2026 UI can place a point from two actual intersecting reference axes. Its save and read-only reopen can distinguish the native tree and keyword owner, point folder or root, visibility and event rows. The alternate two-axis point proves those surrounding owners independently of the fixed data mode. An actual fixed-mode part still requires isolated open and rebuild, point selection and coordinate readback, stock parameter edit, save and fresh reopen against healthy controls. No complete point-bearing SLDPRT, native acceptance, held-out count or corpus conversion is credited here. [Reference point authoring](https://help.solidworks.com/2026/english/SolidWorks/sldworks/t_Creating_Single_Reference_Points.htm) · [InsertReferencePoint API](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~InsertReferencePoint.html)
