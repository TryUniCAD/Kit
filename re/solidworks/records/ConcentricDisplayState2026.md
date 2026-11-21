# Disclosed assembly display state and VisualStates

Task `B04-SW2026-MATES-CONCENTRIC/parent-display-state`, owner `assembly_frontier`, delivery PR #121. This host audit maps the actual configuration, occurrence and file owners in the instance tree and VisualStates archives. The scope covers hash-pinned D01 original and depth edit, frozen and native-saved radial parents, and three independent synchronized native count controls. [Audit tool](../../tooling/sw2026/para/concentric/AuditConcentricDisplayState.py) · [Typed receipt](../measurements/2026/ConcentricDisplayState01.json)

## Instance-tree display owner

The actual selected CMgr object is shared by `f360` and `f368`. Its persistent `f08` equals the XML configuration's `swID`. That configuration owns `swDisplayStateList` and the state leaf. The list and leaf have their own XML-local IDs after the ordinary model inventory. `swObjCount` includes both. The native D01 row carries no explicit `swConfigurationId` on the leaf.

| Measured parent | Config XML ID / persistent ID | Occurrence XML IDs | Persistent occurrence IDs in the list | Display list / leaf XML IDs | VisualStates bytes |
| --- | --- | --- | --- | --- | ---: |
| D01 original | 1 / 0 | 4, 7 | 24, 25 | 8 / 9 | 1,275 |
| D01 depth edit | 1 / 0 | 4, 7 | 24, 25 | 8 / 9 | 1,599 |
| Frozen radial | 1 / 0 | 4, 7 | — | — | — |
| Native-saved radial | 1 / 0 | 4, 7 | 17, 18 | 8 / 9 | 1,142 |
| A12 native empty | 1 / 0 | — | — | — | 597 |
| A13 native single | 1 / 0 | 4 | 24 | 7 / 8 | 1,055 |
| A14 native repeated | 1 / 0 | 4, 7 | 24, 25 | 8 / 9 | 1,247 |

`swCompNameList` supplies the ordered, trailing-comma list of `swReference.swID` values. Those IDs and occurrence names bind the actual `moAssembly_c.f68` list and each `moReference_c.f08`. `swShowState` supplies one action at each corresponding position. Every measured `Yes` slot belongs to an occurrence whose independent XML `swHidden` is `NO` and whose binary hidden word is zero. The component visual attribute matches display mode 6, shaded edges off and display quality 1. The known geometry edit preserves the complete classified XML display subset. The measured native inputs cover the visible polarity. A mixed visible/hidden state and a polarity conflict remain unmeasured.

The existing SDK reads the leaf into `NativeDisplay` and exposes its object ID, label, optional configuration ID and raw leaf attributes in `assembly.attributes["display_states"]`. It separately reads `ComponentInstance.hidden` from each occurrence's `swHidden`. The normal display row has `configuration_id=None` for these nested sources. The list owner and occurrence membership are absent from this public projection. The audit verifies the raw owner graph and the existing public output independently. [Native XML read](../../../src/convert/adapters/solidworks/Assembly/Assembly.py#L812) · [SDK projection](../../../src/convert/adapters/solidworks/Core/Adapter.py#L891) · [Established instance-tree framing](AssemblyInstanceTree2026.md)

## Independent VisualStates owners

`ThirdPtyStore/VisualStates` has its own `visStateKeyData_c` object graph and ID namespace. Its `f118` row joins actual configuration ID 0 to visual state ID 1. That ID indexes the `f0f0` state and the component or feature attribute maps. The state label agrees with the XML leaf where both exist. A12 has a visual state and three visual feature rows even though its XML has no display-state list or leaf. The six stores carry file version 19000, a zero header word named `shown` in the research reader, and `f15c/f158` values 5/0. The state row's three separate words and the two trailing map counts are zero in these controls.

Each component reaches one actual occurrence through its context chain's `moExtFeature_c.f44` and occurrence-name handle. The independent file signature joins the saved parent header. The cache component order is 25, 24 in D01 and 18, 17 in the radial save. The XML vectors use the opposite order. The three component attributes share the same state key. The appearance property object is null, the four state words are `(1, 6, 0, 1)` in field order `f10/f14/f18/f1c`, and the internal label string is `<Default>_Display State 1`. The radial save retains that alias while its actual configuration is named `AssemblyActive`.

The feature rows of D01 and the synchronized controls join Right, Top and Front Plane by `moCompFeature_c.ff0.f00` and each actual plane's creation seconds in `ff0.f08`. Their state words are `(0, 6, 1, 0)`. The native-saved radial control has zero such rows. These separate plane records give no second occurrence polarity case.

All six present streams consume and re-emit every byte with zero tails. The empty parent reaches the provisional displayed-entity tracker. Populated parents additionally reach provisional external-feature serializers. The individual graph reads preserve the provisional status. [VisualStates research schemas](../../tooling/sw2026/serial/defs/Visual.py) · [Visual reference schemas](../../tooling/sw2026/serial/defs/VisualRefs.py)

## Exact D01 edit-save difference

In the original cache, `moExtFeature_c.f10.h18/h10` shares the same file-path and title handles as `moContextChainComponent_c.f40.shared`. In the edited file the former owner matches the edited Header's saved locator and title. The context still holds the original empty locator and `Assem1` title. All other compared typed field values, states, attributes and three plane rows agree across the edit.

| Edited owner | Observed change | Bytes added |
| --- | --- | ---: |
| External parent locator `f10.h18` | Empty to the actual 134-codepoint edited locator | 268 |
| External parent title `f10.h10` | `Assem1` to `ConcentricD01AlignedFree` | 36 |
| Context locator alias | Two-byte reference to its own six-byte empty handle | 4 |
| Context title alias | Two-byte reference to its own 18-byte original handle | 16 |
| Total | Two additional `moCStringHandle_c` objects, map counter 38 to 40 | 324 |

The pair varies geometry and save location together. The measured stream growth is fully accounted for by the two actual file fields and their split aliases. The evidence leaves application precedence, regeneration of that store for custom states, and safe omission open.

## Reproduction and admission boundary

Freeze revision `5f730aea01ccfaaf05594e4acf8cddaf68ea0cc7` with its SDK, research toolbox, three published synchronized parent files and their manifest. Overlay the audit script at its repository path. Run it with locked Python 3.11 as `python -I -B re/tooling/sw2026/para/concentric/AuditConcentricDisplayState.py DISCLOSED_ROOT UNUSED_RECEIPT`. It checks the D01 lock, all seven parent hashes, actual owner joins, stable typed fields, both read and store schema coverage, the exact 324-byte explanation, and five deliberately malformed XML variants.

Whole-source and writer gates retain their existing admission. Independent native evidence would need a configuration that distinguishes two occurrences' visibility in two named states, followed by a healthy fresh-process stale-copy comparison that holds geometry and location fixed while changing only one of the two streams. That would separate visibility polarity, stream precedence and cache regeneration.
