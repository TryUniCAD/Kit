# Model-only assembly display-list composition

Task `B04-SW2026-MATES-CONCENTRIC/parent-display-state`, owner `assembly_frontier`, delivery PR #121. A research composer adds typed authored display names and occurrence visibility to the existing generated `COMPINSTANCETREE`. It takes the actual assembly state, header, child and references already supplied to `MakeAsmTree`, plus an optional `DisplayListIntent`. This tranche establishes guarded host composition. Native writer qualification and precedence between display owners are open. [Composer](../../tooling/sw2026/para/concentric/MakeDisplayTree.py) · [SDK tree constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Xml/MakeAsmTree.py) · [Numeric receipt](../measurements/2026/ConcentricDisplayTreeComposition01.json)

## Field ownership

The pinned native authoring audit joined the XML configuration to the selected CMgr object, and XML references 4 and 7 to persistent occurrence IDs 24 and 25. Its default row and two new mixed rows used `Yes,Yes,`, `Yes,No,` and `No,Yes,` in that persistent occurrence order. The separately synchronized authored pair recovered those same vectors on a warning-free cold open with passing controls. The composition process checks those receipts before it runs. The receipts supply evidence for structure and polarity. The two new generated requests supply their own names and visibility. [Typed native authoring audit](ConcentricDisplayAuthoring2026.md) · [Synchronized cold native read](ConcentricDisplaySync2026.md)

| Wire field | Source |
| --- | --- |
| Owning `swConfiguration` | The config row selected by the ordinary generated assembly. Its `swID` binds the authored intent to the actual `moConfiguration_c` selected through CMgr `f360/f368`. |
| `swCompNameList` | The actual persistent occurrence IDs from the selected root model's generated `swReference` order, checked against `moAssembly_c.f68`, each reference's own `f08`, and its external-feature backlink. |
| `swDisplayStateName` | The authored name in each ordered `DisplayStateIntent`. |
| `swShowState` | The authored booleans looked up by persistent occurrence ID in generated tree order, encoded as `Yes,` and `No,`. |
| List and leaf `id`, root `swObjCount` | The next IDs after the complete generated XML-local inventory and the resulting node count. The list precedes its ordered leaves. |

The research guard admits one active configuration and two direct ordinary visible, unsuppressed and rigid occurrences. It requires each state to cover both actual persistent IDs once. The first state agrees with the unchanged all-visible default occurrence fields. An omitted display intent returns the exact existing SDK bytes. The lower-level append function also accepts the unframed generated DOM for a future construction call site. The research wrapper composes only the DOM that its own call to `MakeAsmTree` just generated.

## Guarded host receipt

The proof uses two independently authored ordinary neutral parents and their generated parts. The second uses the existing typed empty exploded manager. Its additional persistent allocation changes occurrence IDs from 17 and 18 to 18 and 19. Both cases retain XML occurrence IDs 4 and 7. The authored input vectors deliberately supply members in different orders, and the emitted vectors follow the selected model references. A name containing `&` and a name containing `Ω` survive normal XML and SDK raw readback.

| Generated configuration | Persistent occurrence IDs | XML length without intent | One all-visible state | Three states including both mixed vectors |
| --- | --- | ---: | ---: | ---: |
| `Shop layout` | 17, 18 | 2,054 | 2,231 | 2,403 |
| `Fixture review` | 18, 19 | 2,074 | 2,251 | 2,423 |

The baseline root has seven XML-local objects. The list consumes ID 8 and the leaves use the following IDs up to 9 or 11. Four in-memory container compositions alter only `COMPINSTANCETREE`. Removing the generated list and restoring the computed count recovers the complete baseline XML byte for byte. The SDK's existing typed display read admits each single all-visible state, and its raw read recovers all three rows for each mixed case. The same guard refuses foreign config IDs, XML-local IDs used as members, duplicate or missing members, reversed native references, duplicate names, and a hidden default conflicting with the generated owner.

The two neutral constructions and their independent repeats ran under the existing `BuildAudit` process guard with zero recorded runtime file or process access. The proof wrote no CAD files and launched no CAD processes. The existing adapter registration, VisualStates construction and typed mixed-state read remain outside this tranche. [Host proof](../../tooling/sw2026/para/concentric/ProveDisplayTreeComposition.py) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveDisplayTreeComposition.py \
  > /tmp/ConcentricDisplayTreeComposition01.json
```

The retained receipt SHA-256 is `aa96f0c82562e578d53561928501e4ad8584011b2bb0639a08b2250b38a25905`.
