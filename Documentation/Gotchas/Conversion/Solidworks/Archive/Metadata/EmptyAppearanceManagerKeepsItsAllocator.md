# An empty appearance manager keeps its independent allocator

## Expectation

Two parts with equal display-state stores and empty Definition appearance lists share the same next appearance ID.

## Actual behavior

In the two disclosed SOLIDWORKS 2026 rectangle children, the holder appearance is byte-identical and both Definition lists are empty. The live model and selected configuration use RealView IDs 9 and 10 respectively. Their Definition manager next IDs are 10 and 11. Both holders use ID 3. The stock appearance locator spelling also differs between live owners and the detached holder. [Exact typed readback](../../../../../../re/solidworks/records/SdkPlanarVisualComposition2026.md#actual-child-appearance-owners)

## Workaround

Read the live appearances, holder and Definition manager independently. Preserve the recorded allocator when re-emitting a typed source. Fresh construction needs independently known assignment and allocation rules before it can express this populated appearance. [Related empty wrapper scope](../EmptyDefinitionRendererWrapper.md)
