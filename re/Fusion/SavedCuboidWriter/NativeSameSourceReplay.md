# Native same-source cuboid replay evidence

Fusion 2706.1.17 opened, rebuilt, edited, saved and reopened the exact baseline research archive `c05251997755d8c68a0e8ba14db5ccf248a6ca5b1a610434f51a9801b4d0ce32`. The archive came from typed re-emission of the persisted complete read-only JSON for native source `b6726c11bd4e67155035de7fc6bcda3b559682fc9c4f496c2b35a05d84184752`. The procedure is in the [oracle preparation guide](../LocalOracle/SavedCuboidRoundTrip/README.md).

The bracketing independent geometry control was `5f9ad382c5e4b15313a59bebe4201ccd5b87137a3f20ebe85f5e3fba79148ca0`. It used steel. The measured candidate used Kit Generic Material. The comparison covers geometry, timeline, editability and basic mass. Same-style control comparison, displayed appearance, per-face selection and viewport or embedded-preview behavior still need measurement.

| Stage | Fresh process | Open documents | Raw receipt SHA-256 |
| --- | ---: | --- | --- |
| Control before | 1 | 0 → 0 | `eb590e51690f80545f265273e0992ead5cc51d6aba6f40cd1b7e266cafac15fa` |
| Candidate | 2 | 0 → 0 | `c6730e8506216539cac410fa1989dd21d86b90a01751c54fcf09318797d269d5` |
| Reopen exact saves | 3 | 0 → 0 | `229c108ad84f47fe5ce8da94810a413c31339022eb7acb05196e6ed82e0647c8` |
| Control after | 4 | 0 → 0 | `9a8ebc4430e167f2d3ecc45363b595d615ffb3d24bd4be420405f827a82c722e` |

The four fresh process checks passed. The baseline geometry is 16.4 × 27.1 × 13.8 mm. Original and rebuilt volume was 6.133272 cm³, with center (0.82, 1.355, 0.69) cm. The native edit to 28.3 mm yielded 12.577652 cm³ and center (0.82, 1.355, 1.415) cm. Restoration returned to the original values. Rollback, edit, restore and both exact native save reopens passed.

| Native save | SHA-256 | Height |
| --- | --- | ---: |
| Edited | `24f2c0e7714e3c234ead298c842b118a828ac7a3d6f6b48b9f924a8af0926ac5` | 28.3 mm |
| Restored | `98341de3b091096939a86b8b00f5da016f76b2acffdd5e8ff5e2a636797972df` | 13.8 mm |

The SDK at `43b2a10c4bd3f02832b98404878be8c738ec1625` strictly opened both saves and reloaded their full typed state through persisted JSON with exact document equality. Both retained the read-only marker. The reported neutral volumes were 12,577.652 and 6,133.272 mm³. Full receipts and native save bytes remain in local research storage under `.rescratch/FusionSavedCuboidOracle/ReplayBaselineReady`. The [sanitized receipt](NativeReplayReceipt.json) keeps content digests and stage measurements. The private derived receipt index SHA-256 is `c235001dbf6b0e90af98e616bf6d0e10a5336444e4020986619172a76e1fb7f6`.

The one-member graphic and material contrasts still await native review. A new task-owned auxiliary session failed before authoring because Fusion exposes the root component name as read-only in an untitled design. It closed with zero open documents. The launch guard then found a new unowned Fusion process and stopped before dispatch. The prepared capture removes only the attempted decorative name assignment. See the [untitled root name gotcha](../../../Documentation/Gotchas/Conversion/Fusion/Api/FusionUntitledRootName.md) and [presentation and validity checks](PresentationOraclePlan.md).

The measured archive reuses its own decoded source state through the existing typed emitter. The product writer still requires independent generation from the supported authored graph, preservation of all required state, and full native controls under the [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
