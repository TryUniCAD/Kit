# Native tree parity requires the authored datum labels

The neutral document stores support-plane identity in `SupportPlane.id` and its visible label in `SupportPlane.name`. A native tree comparison expects the visible label present in the original authored model. The SOLIDWORKS two-stock writer preserves the supplied neutral label on its actual fixed support.

In the first locked two-stock comparison, the evaluator populated both labels with internal IDs. Every geometry and edit check passed. Two generated native tree rows carried the internal labels. The source authoring tool had selected `Front Plane` and `Right Plane`, so both cases failed the exact tree comparison. [Original comparison](../../../../../../re/solidworks/measurements/2026/TwoStockWriterHoldoutNative01.json)

Project the original authored labels alongside the support IDs and signed frames. The corrected evaluator used the pre-writer authoring tool's pinned labels and kept the original writer source tree unchanged. Both full native trees matched in every snapshot. [Controlled recheck](../../../../../../re/solidworks/measurements/2026/TwoStockWriterHoldoutNative02.json)
