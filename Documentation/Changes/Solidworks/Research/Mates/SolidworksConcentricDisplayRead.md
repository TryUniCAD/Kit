# Read typed assembly display-state visibility

The SOLIDWORKS reader exposes `assembly.attributes["typed_display_states"]` for the measured ordinary single-state profile. It binds the actual configuration, list and ordered occurrence IDs from the component tree to the binary configuration and live references. One or two direct occurrences with the measured visible action are supported. The existing raw display rows and legacy name fallback remain available.

Paired host SDK reads check all seven disclosed parents, the linked original and edited D01 and radial paths, and deliberately malformed ownership or polarity. The typed view survives absent and unreadable VisualStates stores in host diagnostics. Native writing and stream precedence remain unqualified. [Contract and exact host evidence](../../../../../re/solidworks/records/ConcentricDisplayRead2026.md)
