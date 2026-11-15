# Initial assembly configurations contain a componentless state

An assembly without inserted components still needs more than two configuration
option objects. The native active configuration-manager constructor also
constructs a `moConfigObject_c` with a null component and inserts it into the
initial configuration's state collection.

In SOLIDWORKS 2026, `sldmodu.dll!0x4b8802f0` creates the two distinct option
objects passed to configuration constructor `0x4b8c4f30`. It then creates a
third option profile, passes it to component-state constructor `0x4b8a5230`,
and inserts that state through virtual `+0x1f90`, target `0x4b8c9450`.
The component-state constructor owns a clone of its options. Reusing one
options object for all three relationships contradicts this ownership graph.

Construct the componentless state and three separate options allocations from
the native rules. Do not infer an empty state collection from a model's zero
visible component count. Later component insertion and configuration cloning
have separate transitions and must not be replaced by this initial profile.

The [construction record](../../../../../re/solidworks/records/AssemblyConstruction2026.md#initial-assembly-configuration-graph)
binds the addresses to module hashes and records each emitted field. This is
static evidence; generated-assembly load, rebuild, edit and final cache
acceptance remain unproven.
