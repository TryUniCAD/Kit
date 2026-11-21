# Through-all empty document managers

The internal source component now constructs the actual empty BOM and rendering managers from typed semantic state. It preserves explicit BOM presence and the source rendering allocator, with every signed word, object/class tag, count and reference map computed by the shared SDK rules. Existing default/source-view writers remain unchanged.

Use `ReadThruMgrs(document, link, definition)` on the same complete ordinary source archive, then pass the resulting `EmptyMgrInput` to `MakeThruMgrs` with the existing owner/configuration/view inputs. The result remains an incomplete `ThruConfigGraph`. Populated or unknown manager state, mismatched counts/rows and invalid presence/counters refuse. No full-source or public writer gate is opened.

The frozen host method passes 80 fresh processes: 37 genuine SDK rejections, 56 independent fragment round trips and 12 additional owner-inventory stream re-emissions. Three disclosed source manager states and five independent presence/counter variants persist exactly. Earlier source cameras, member fragments and complete ordinary public callers remain unchanged. Nine SDK modules pass static checks and the donor scan. Definition still has 10 unrepresented frontiers per source and CMgr still has 29; no new native lifecycle is claimed.

[Guide](../../../../../Reference/Research/Solidworks/Construction/ThroughAll/EmptyManagers.md) · [Native/source record](../../../../../../re/solidworks/records/ThroughAllEmptyManagers2026.md) · [Host receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllEmptyManagers01.json) · [Lazy-getter gotcha](../../../../../Gotchas/Conversion/Solidworks/Model/ThroughAll/BomGetterAllocatesManager.md)
