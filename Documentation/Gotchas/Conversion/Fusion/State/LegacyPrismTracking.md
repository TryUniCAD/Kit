# Dataclass defaults do not migrate stored prism JSON

## Expectation

Adding an empty default to `PrismHistory.Tracking` lets the constructor restore older neutral JSON that omits that field.

## Actual behavior

The semantic-state decoder checks the complete field inventory before invoking a constructor. A dataclass default therefore does not make an older field inventory compatible. The writer rejects an older cuboid export before reconstruction.

## Workaround

Register the empty tracking value in the explicit semantic-state defaults registry. Merge stored values afterward so explicit source identities retain precedence. Keep the exact field inventory check to reject unknown or missing required fields.

Omit the newly optional tracking field when it is empty during encoding. Emitting a redundant empty field changes the complete neutral JSON fingerprint of older documents. Preserve nonempty tracking without omission. The encoder uses a declarative omission registry, while the decoder accepts either inventory.

The public compatibility case writes a cuboid, removes only the newly added tracking field from its stored state, and writes the older layout through the public API. The restored archive must be byte-identical and retain its feature timeline. See [the change entry](../../../../Changes/Fusion/Reading/FusionSavedPrismEdits.md).
