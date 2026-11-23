# Assembly content-index mate descriptor

Task `B04-SW2026-MATES-CONCENTRIC/source-content-index-mate` in PR #121, owner `assembly_frontier`. The implementation base is `935d9848dab052aff0bc4495faa579e011cc7cba`. The exit for this slice is exact reproduction of the ordinary `moBCMate_c` record from its real configuration, mate and endpoint owners. [Linked assembly archive](AssemblyArchive2026.md#cache-and-auxiliary-nodes) · [Disclosed paired-source custody](../measurements/2026/ConcentricD01PropertyTransport01.json)

## Format and owners

The content index has one `moBCModeInfo_c` root. Its actual active configuration is the `moBCConfigurationInfo_c` whose name and persistent ID join the current CMgr selection. Under that configuration's object map, the assembly's `moBCNode_c.f50` holds the ordered descriptors. Each descriptor represents one actual mate in the inherited `Contents/Config-0-MatesList` graph.

| Member | Classification | Ordinary two-end rule |
| --- | --- | --- |
| `f08` | Input | Name of the actual active assembly configuration from its typed name owner. |
| `f10` | Constant | Initial zero from the base class initialization. |
| `f18` | Input | Actual mate feature name. |
| `f20` | Derived | Active-configuration suppression value. The ordinary absent configuration object gives 2. |
| `f24` | Derived | Concrete mate kind. Coincident is 0, concentric is 1 and distance is 5. |
| `f28` | Derived | Exact registered class name of the mate. |
| `f30` | Derived | Mate name followed by one space and both ordered occurrence display labels in parentheses, joined with a comma. Each ordinary live occurrence's last `-number` becomes `<number>`. |
| `f38` | Constant | Zero on the ordinary branch. The distinct in-place construction assigns 1. |
| `f3c` | Derived | Actual mate feature's persistent node ID, `mate.f08`. D01 happens to allocate 26. |

Each selected wrapper is in `mate.f410` order. The wrapper must carry the actual mate ID, its owned selection slot, and a distinct allocated wrapper ID. The component reference chain must reach an actual member of the parent. Its external backlink must resolve to the same occurrence and agree with the occurrence's typed name. The display transformation uses the last numeral suffix in that name. Both D01 occurrence fields `f3f8` are 101, while their display instance numbers are 1 and 2. The detached support list and both mate strings `f488` and `f490` have independent roles. [Descriptor constructor](../../tooling/sw2026/para/concentric/AssemblyMateDescriptor.py) · [Occurrence name grammar](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Xml/ReadOccName.py)

The constructor checks concrete schema and direct owner identity. It refuses foreign configurations and groups, explicit configuration overrides, unknown mate classes, and malformed or reused selected wrapper identities. It currently covers only the ordinary active two-end content-index descriptor for the three listed types.

## Exact-build authority

Native static observations use the installed SOLIDWORKS 2026 SP05.2 `34.5.2.0604` x64 `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Addresses are preferred-image VAs.

- The `moBCMate_c::Serialize` field order starts at `0x4b73f570`. Its factory reaches the constructor at `0x4b73b160`, which initializes the inherited and in-place words to zero.
- The ordinary mate cache branch at `0x4b73dc6c` obtains the live feature name through virtual slot `+0x88`, the persistent ID through `+0x188`, the attribute kind through `+0x2180` and the registered class through `GetRuntimeClass`. The exported `getNodeId@moBCMate_c` independently returns `+0x3c` at `0x4b2a7590`. The exported type and suppression accessors return `+0x24` and `+0x20` respectively. The special in-place route sets `f38` at `0x4b73dba6`.
- The active configuration name is assigned at `0x4b73dd3b`. Suppression calls the active configuration's actual `getObject` with the mate node ID at `0x4b73dd75`. If present, the object contributes `2 * ((~f0c) & 1)`. Otherwise the native branch supplies 2. The constructor supports the measured ordinary absent-object case.
- The dispatcher at `0x4b73dd16` passes browser flags `0x35` to mate virtual `+0x3a8`. The three concrete mate vtables resolve that to `0x4bc382a0` and the ordinary selected-reference display slot `+0x1fc8` to `0x4bc4d7f0`. That producer follows both actual `+0x410` selections in order. The direct occurrence label path at `0x4bc79d60` splits the ordinary occurrence name and supplies the angle-bracket suffix. The two-name concatenation at `0x4bc4de91` uses the literals ` (`, `,` and `)`. The latter text is appended to the mate feature's browser name. This is the live descriptor producer, distinct from the exported stored-string getter on `moMateParent`.

## Process evidence and scope

The [offline proof](../../tooling/sw2026/para/concentric/ProveAssemblyMateDescriptor.py) verifies the six original/edited D01, D02 and D03 parents and the four A0, A1, A13 and A14 controls by source digest. It decodes and writes their full content indexes, linked mate lists and configuration managers. It then substitutes fresh generated descriptors into the decoded **comparison** graph and verifies whole-stream byte identity. All ten indexes match after replacing nine descriptors. The D01/D02/D03 descriptors retain their IDs and labels across the actual edits. A1 supplies three independently observed records with IDs 26, 28 and 29. The three no-mate controls retain their empty lists.

Two fresh isolated processes receive only neutral intent over standard input. They reproduce the previously measured 10,760-byte persistence parent and 10,839-byte child exactly. The second authored graph changes the active configuration and mate display name, assigns unrelated two-part labels, sets rotation lock and reverses the actual selected endpoints. Its computed display text is `Opposite axis 検 (Other-mount<3>,Motion-guide<17>)` and its child bytes remain identical. Both graphs allocate the mate ID 19. The genuine archive round trips recover each new descriptor and six malformed or unsupported cases refuse. The active audit records zero writer input accesses. [Digest-bound receipt](../measurements/2026/AssemblyMateDescriptor01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveAssemblyMateDescriptor.py \
  --disclosures /path/to/Oracle121Takeover > /tmp/AssemblyMateDescriptor01.json
```

The surrounding content index still needs its own model-derived treatment. Native lifecycle and held-out qualification for emitted indexes remain pending.
