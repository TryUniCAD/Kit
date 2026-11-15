# Reference stamps copy target state

An ordinary component reference does not retain all of its constructor's update
stamps after insertion. Its placement stamp also has a separate owner and
lifecycle.

The 2026 ordinary insertion path calls `setModelUpToDate`. With an available
part target, that method copies the target header's update counter and time.
It also copies the target model's geometry-change stamp. The part-target
component-transform getter returns literal 101. Assembly targets use different
aggregation methods and do not inherit that literal rule.

Derive reference updates from the actual generated target and its header.
Keep placement changes separate from target model updates. Do not fill every
stamp with 101, derive stamps from component count, or reuse a captured time.

The [construction record](../../../../../re/solidworks/records/AssemblyConstruction2026.md#reference-update-state-after-insertion)
records module ownership, virtual slots, constructor seeds and native methods.
The conclusion is static evidence. Complete fresh reference construction and
held-out native assembly acceptance remain unproven.
