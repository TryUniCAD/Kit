# Empty SOLIDWORKS 2026 advanced part property owners

Task B04-SW2026-PARTPROPS. Owner `/root`. Delivery PR #121. Dependency [the exact property source grammar](PartPropertySources2026.md). The scoped exit is exact SDK `Contents/CusProps` readback, current compatible text projection, and explicit rejection of populated or unknown ownership.

## Version-19000 field order

| Owner                            | Fields in serialized order                                                                                                               | Ownership and current limit                                                                                                                                                                  |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `moCusPropMgr_c`                 | Signed32 `f0c`, signed32 `f08`, unsigned32 `n20`, keyed `f20` rows, unsigned8 `f54`                                                      | Rooted schema one with independent map base 1. The row count follows actual ownership. The two admitted empty policy states below are read boundaries.                                       |
| `moCusPropContainer_c`           | Tagged `f08`, `f10`, `f18`, then signed32 `f20`                                                                                          | The first two own the concrete file and cut-list scopes. Empty advanced admission requires a null extra owner and zero trailing policy.                                                      |
| `moFilePropContainer_c`          | Tagged `f08`, `f10`                                                                                                                      | Actual document and configuration lists. The empty profile requires both null.                                                                                                               |
| `moCutListPropContainer_c`       | Unsigned32 `n08`, keyed `f08`, unsigned32 `n38`, keyed `f38`                                                                             | Both actual row collections must be empty.                                                                                                                                                   |
| `suObList`, `moAdvCusPropList_c` | Framework count and tagged object rows                                                                                                   | Counts and identities follow the measured collection.                                                                                                                                        |
| `moAdvCusProp_c`                 | Embedded `suObList f10`, signed32 `f08` and `f0c`, CString `f58`, signed32 `f7c`, CStrings `f60` and `f70`, signed32 `f78`, `f80`, `f84` | The measured literal case connects the name, type, expression and value to the string element. Other control values retain their exact owned representation pending semantic classification. |
| `moCusPropStringElem_c`          | CString `f08`                                                                                                                            | Actual string element input.                                                                                                                                                                 |

Every keyed row starts with its signed32 key, followed by a tagged object. The SDK consumes the full graph. The compatibility manager admits policy `(-1, 0, 0)` and no rows. The present empty manager requires policy `(-1, 1, 0)`, one row with key 0, a concrete file child and empty property scopes. The cut-list child may be null or a concrete schema-one cut-list container with both row collections empty. Other state remains guarded.

## Verification

The [six fresh public SDK reads](../measurements/2026/SdkPartPropertyManagerRead01.json) re-encode the complete manager through the shared archive model. The 33-byte compatible control ends at map counter 3. The four 138-byte saved empty advanced managers end at counter 9 and return compatible literal-text status. The 697-byte populated control ends at counter 23 and retains its explicit unsupported status. The [original property measurement](PartPropertySources2026.md) and [separate part naming measurement](PartDriverAndBodyNames2026.md) bind source custody and native saves.

The generated public-reader regression keeps exact document and configuration text when the empty advanced owner is present. An otherwise identical file with an unknown policy rejects its optional text projection and retains geometry and history. The scoped work adds no writer family or FCStd qualification.

## Ordinary native imports

Four disclosed local BaseBody files contain the same fully consumed
102-byte manager stream, SHA-256
`22ecc7dd4564532e71f54ca4b59e9aee9c6e98c62a2f9c7fecc6fe72d793134e`.
Their concrete file child has null document and configuration lists,
their cut-list and extra-owner references are null, and the trailing
policy equals zero. The healthy parametric control retains the previously
observed 138-byte representation with both child objects.

The corrected reader publishes the three genuinely empty compatible
text scopes. An exact SDK comparison against the earlier reader observed
only the new empty bags, their status, the obsolete diagnostic removal
and the derived source semantic hash. All other document fields,
including the feature timeline, B-rep and embedded payloads, matched.
Wrong cut-list classes, populated cut lists, missing file owners and the
native advanced property control still refuse projection.
[Host measurement](../measurements/2026/ImportedLocalPartSemantics01.json)
[Nullable cut-list gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Properties/EmptyImportPropertyManagerCanOmitCutList.md)
