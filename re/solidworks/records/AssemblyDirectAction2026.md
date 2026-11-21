# SOLIDWORKS 2026 assembly direct header action

Task `B04-SW2026-ASSEMBLY-HEADER-ALIASES` delivers the direct writer owner
repair from [aggregate revision 3136c93c5](https://github.com/TryUniCAD/Kit/commit/3136c93c5d5f30395d315a2124894cc60de9d9cc)
on accepted main `91df941c98d2e96633eb0fd0f0a1adfbf70d3039`. The emitter
shares the existing reader owner table for version 19000. It checks
writer depth one, a registered root object and distinct unallocated
`moExtObject_c` schema-one aliases.
[Change entry](../../../Documentation/Changes/Solidworks/Archive/Configuration/SolidworksAssemblyHeaderAliases.md)

## Physical owner and map

The saved `moAssembly_c.SerializeLWData` section inherits
`moModel_c.FUN_4c22ec80`. Its first base call,
`moModel_c.FUN_4c17aa00`, binds header objects before the first two
stored words, `fb0` and `fb4`. The operation consumes no bytes.
The physical header objects come from `f38` self followed by the
`f30` directory, in its stored order.
[Assembly field layout](https://github.com/TryUniCAD/Kit/blob/3136c93c5d5f30395d315a2124894cc60de9d9cc/src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/Assemblies/AssemblyFields.py)
· [Shared model layout](https://github.com/TryUniCAD/Kit/blob/3136c93c5d5f30395d315a2124894cc60de9d9cc/src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/ModelFields.py)

The guarded native-prefix probe takes two disclosed saved assemblies from
their pinned Git objects. The production envelope and ModelHeader reader
load the complete header graph. The production section and direct
actions operate on the actual top-level assembly descriptor and its
bounded lightweight child before stopping after the first two scalars.

| Source | Header object slots in order | Direct interval | Configuration slots | Base and next counter | Lightweight and resolved windows |
| --- | --- | --- | --- | --- | --- |
| `A0_one` | 69, 65 | [22, 22) | 3, 4 | 5, 5 | [22, 3133), [3137, 24828) |
| `A1_two` | 80, 73, 77 | [22, 22) | 3, 4, 5 | 6, 6 | [22, 3643), [3647, 25338) |

Both inputs start the action with map base 1 and counter 3. The
prefix has values 0 and 19000 and ends at offset 30. Stored header indices
and allocated configuration slots carry the same object identities.
The mate payloads are accounted for by digest and length. Full Config
and MatesList replay still needs the assembly body layouts and linked
mate executor on main.

## Independent writer boundary

The separate author process constructs typed headers and top-level assembly
objects from independent model values. The checked byte formulas cover
38-byte and 40-byte frames, directory order, zero-width direct fields,
and link tags in a later sibling section. A fresh reader verifies
the links resolve to the original header objects and checks exact
consumption. Both processes deny file and external access during
archive processing.

Six refusals cover the old archive version, nested and detached assemblies,
and missing, duplicated, or previously mapped aliases. The old main
code refused the positive assembly at the direct action. The repaired
code retains the existing part and ghost bytes. The previous wrong-owner
test now uses an unrelated name object.

From the checkout root, run the [guarded probe](../../tooling/sw2026/CheckAsmDirect.py).
Use `measure-native` when the [pinned source revision](https://github.com/TryUniCAD/Kit/commit/5554733fde548afabdc6db221f387163d15e9497)
is available in the local Git object database.

```sh
python3.14 -I -B re/tooling/sw2026/CheckAsmDirect.py measure
python3.14 -I -B re/tooling/sw2026/CheckAsmDirect.py measure-native
```

The [current receipt](../measurements/2026/AssemblyDirectAction01.json)
binds these action-level observations to source and parser hashes.
The [earlier aggregate result](https://github.com/TryUniCAD/Kit/blob/2052e6ef14b5635502c41117deb950e4ac9aff2a/re/solidworks/measurements/2026/ArchiveAfterSectionMerge01.json)
recorded exact Config and MatesList replay for eight native assemblies
and 1,328 exact streams across the whole disclosed audit. That broader
replay used the aggregate codecs. The [queue case](../../../tests/Convert/Solidworks/Configuration/Sections/AssemblyAliasTests.py)
uses the source-free action proof on main.
