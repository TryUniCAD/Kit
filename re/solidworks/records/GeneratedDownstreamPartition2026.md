# Generated downstream IDs on part topology

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is owned by `/root` and delivered in PR #121. The research projection generates the two downstream kernel attributes on an ordinary solid part. Both the rectangular boss and circular boss use the shared allocator and the existing active and rollback partition machinery.

The pinned Parasolid 37.01.250 implementation reads the body edge chain first. It then traverses the regions and shells to append each shell's edge chain. The face enumeration visits those regions and shells in the same order and follows each shell's face chain. The array getters and initial iterator paths use those links. The generator checks each member's kind and owner and follows the actual links even if the input node table is reordered. [Kernel traversal and three disclosed readbacks](ParasolidBodyTraversal2026.md)

The fresh data object starts its counter at one. Face creation consumes the first identifiers and edge creation consumes the following identifiers. The result keeps each identifier tied to the owning topology object. The installer checks the order and full coverage before attaching the records. The fresh rule covers the initial allocation. Rebuild reuse requires the retained semantic model cache. [Native counter and ownership rules](DrawingDownstreamIdentity2026.md)

| Field | Derivation |
| --- | --- |
| Owner | The model session supplies its UUID once. Hash the canonical text as UTF-16 code units with bases 32771 and 32779, each modulo 1000000009. |
| Identifier | Use the shared counter at the current face or edge in the linked traversal. |
| Update time | Use the actual UTC seconds and 100 ns ticks of the model session, converted to FILETIME. |
| Context | Emit zero for the ordinary part. The native field records the model's assembly flag. |
| Kernel integer words | Emit the identifier, FILETIME low and high, context, then owner key low and high. The six signed words preserve their unsigned bit patterns. |
| Model-cache owner fields | The owner text is followed by the key's high word and low word. |

At `sldgciParau!0x32fa0943`, the edge definition calls the same integer definition constructor `0x32f9c400` as the face definition. Both pass three slots and the same ordinary persistence arguments. The edge definition chooses the actual edge owner class. The six integers are one value array in slot zero. The optional projection supplies the two remaining slots as null. [Slot layout](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/DownstreamAttributeSlotZeroCarriesSixWords.md)

## Replay

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m drawing_edges.CheckDownstreamPartition prism 1
```

Run with `prism` or `cylinder` and case `1` or `2`. Eight fresh processes reproduce two rectangular and two cylindrical partitions, including active and rollback bytes. They check all six words for each actual owner against independently packed values, read the outputs back, refuse malformed links and reject allocations with foreign or misordered edges. The four complete generated partitions have different lengths. Eight further processes compare the existing untagged rectangle and cylinder paths against the previous revision.

The measured result covers generated partition attributes and exact host readback. Current-schema pointer fixup retains the exact registered topology slots. Full receive normalization remains open. [Receive source record](ParasolidReceiveChainLinks2026.md) · [Partition process receipt](../measurements/2026/GeneratedDownstreamPartition01.json)

The 64 published examples all decode and contain zero per-configuration downstream caches. The standalone cache codec now replays all 18 counted sections with the fresh archive map on modeled input. A dedicated disclosed cache still needs byte-exact replay with its actual reference graph. The linked drawing edge graph and native open, rebuild, edit and reopen remain open. [Standalone cache codec](DownstreamStandaloneBodyCodec2026.md)
