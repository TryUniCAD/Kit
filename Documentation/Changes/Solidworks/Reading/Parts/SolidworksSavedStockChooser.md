# Verify the chooser for a saved stock selection without a face carrier

The internal SOLIDWORKS 2026 two-stock reader recognizes a saved selected wrapper with no `ff0` face and zero `f100` and `f104`. The existing selected atom and self-component checks run first. The chooser branch checks both of the cut's distinct face pairs against the actual linked archive map. Their ordered references use the selected stock's actual external owner, two stock caps, stock sides and the cut's actual free-circle marker.

The original disclosed save still follows its face-carrier path. The edited derivative passes the isolated chooser check and binds the surviving atoms to their active partition bodies. Its full SDK read still reaches the extrusion-mode refusal. The 12 guarded processes verify both save shapes, ten altered ownership refusals and identical public document digests to the baseline. All recorded zero runtime external accesses.

```sh
python3.14 -I -B re/tooling/sw2026/throughsource/ProveStockPick.py \
  --selected /path/to/ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT \
  --edited /path/to/GeneratedTwoStockGraph01/NativeAfterEdit.SLDPRT
```

[Exact process receipt](../../../../../re/solidworks/measurements/2026/TwoStockSavedSelector01.json) ·
[Source audit guide](../../../../Reference/Research/Solidworks/Construction/ThroughAllSources.md) ·
[Selector gotcha](../../../../Gotchas/Conversion/Solidworks/Model/ThroughAll/SavedStockChooserMayLackFace.md)
