# Visual state maps use their outer state keys

On the saved SOLIDWORKS 2026 assembly with opposite named visibility
states, the component attributes under outer state keys 2 and 3 retain an
inner owner field of 1. Their shared display-state alias also points to 1.
Joining by those inner values associates the mixed visibility rows with
the default state.

Join the outer key through the actual state table and the component map
through the persistent occurrence. Preserve the separate inner values and
object aliases during typed re-emission.
[Saved row and byte comparison](../../../../../re/solidworks/records/ConcentricDisplayAuthoring2026.md)
