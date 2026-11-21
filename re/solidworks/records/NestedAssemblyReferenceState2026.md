# Ordinary subassembly reference state in SOLIDWORKS 2026

The ordinary external-reference constructor and load route are shared by resolved part and assembly placements. The target's concrete model changes configuration selection and two update stamps. These are static bindings in SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. All addresses in this record use preferred image coordinates of `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. [Ordinary occurrence fields](OrdinaryOccurrenceConstruction2026.md) · [Original reference constructor](AssemblyConstruction2026.md)

## Resolved target dispatch

`moReference_c` table `0x4cf7a8b0` binds `+0x1c98` to `0x4bbc71a0`. In the ordinary path that function resolves the actual target through `+0x1cc0` at `0x4bbc7216` and dispatches target `+0x1a8` at `0x4bbc7231`. The assembly table `0x4ce69b30` returns true through `0x4b27e150`. The part table `0x4d1252d8` returns false through `0x4b27cbe0`. `moConfiguration_c::getOrAddObject` chooses `fc48` for the true result and `fc50` for false at `0x4b8d162f` through `0x4b8d1652`. The selected object is copied into the occurrence's configuration record. If the live target is unavailable, the reference predicate reaches its separate external directory kind check at `0x4bbc71f1` through `0x4bbc71fa`, where kind `3` means assembly.

`moReference_c::setModelUpToDate` at `0x4bbcf680` uses the following virtual getters on the resolved model. The field layout remains that of `moReference_c`.

| Occurrence field | Target slot and assignment | Ordinary subassembly target |
| --- | --- | --- |
| `f3e0` | `+0x1030` then store at `0x4bbcf6d2` | `0x4bdac640`, same header update counter as part |
| `f3e8` | `+0x1248` then store at `0x4bbcf6f0` | `0x4bdac6a0`, same header modification time as part |
| `f3f4` | `+0x19e0` then store at `0x4bbcf743` | `0x4b55ff40`, assembly geometry change stamp |
| `f3f8` | `+0x19d8` then store at `0x4bbcf755` | `0x4b55fdd0`, assembly component transform stamp |

## Distinct stamp operations

`getComponentTransformStamp` starts at `101` and traverses the target assembly's live direct-reference set at `f15e0`. Each reference's `+0x16f8` selects `0x4b541640`, which returns its own `f3f0`. The accumulator compares equal to `101` at `0x4b55fe7d` before each contribution. It takes the incoming value in that branch and adds it otherwise. An empty direct set retains `101`. For a nonempty fresh set in which every direct placement explicitly received stamp `102`, the result is `102` times the number of direct occurrences. This is a fold over that definition's placements. [Fresh placement stamp](AssemblyConstruction2026.md#reference-update-state-after-insertion)

`getGeometryChangeStamp` starts with the assembly's own `f1300` at `0x4b55ffd9`. The zero-argument branch walks the live direct-reference set. It resolves each existing child at `0x4b5600c5`, checks an ancestor set, then calls child `+0x19e0` with an independent copy of that set at `0x4b56020b`. It adds the resulting 32-bit stamp at `0x4b56022b`. A resolved acyclic hierarchy therefore adds the target geometry stamp once per occurrence. A part contributes its own `f1300`. An assembly contributes its `f1300` and its recursive child contributions. A repeated reference shares its target model and still contributes per occurrence. The two getters use independent reset and diagnostic branches. This record covers ordinary fully resolved acyclic graphs and the setter's zero-argument path. The live-reference-set population and serialized cache behavior still require the nested native sources.

The native exception ranges and SHA-256 fingerprints for the four traced functions are listed below. The discovery cohort will compare each enclosing reference's persisted stamps against its actual loaded dependency closure.

| Function extent, end exclusive | SHA-256 |
| --- | --- |
| `0x4bbc71a0–0x4bbc7245` | `ecef015f0d28c2ee373414b14a95a4427f70ebda54fdb149979b588c15ab3f67` |
| `0x4bbcf680–0x4bbcf85e` | `b35e469b1e1860b78607a9e0b46571440f5e46ce4b44295642b5ca22ef27372e` |
| `0x4b55fdd0–0x4b55ff2b` | `96b43071c14c6020a350b06b9d3b80a728ee882ad403452f02ec4b225e4e30c2` |
| `0x4b55ff40–0x4b5602d5` | `77581200fa3b92c78c3a6c7325d3e87d6e06aa37c14ebf87bf3afe61789aa0af` |

## First writer boundary

The research composer and XML indexes currently specialize their child input, local bounding box and external directory to one generated part. The public reader has nested definition and occurrence mapping, including matching by canonical basename, configuration and native type. Its ordinary validated 2026 examples remain flat. The first nested writer needs a generated subtree with its true `moConfiguration_c`, sibling file metadata, assembly-local box and the applicable stamp sources. Validate direct Config-0 references, CMgr context path lengths and options, both parent bounding boxes and the nested XML closure against the source cohort before choosing their construction rules. [Current flat metadata graph](AssemblyInstanceTree2026.md) · [Nested source procedure](NestedAssemblySourceProtocol2026.md)
