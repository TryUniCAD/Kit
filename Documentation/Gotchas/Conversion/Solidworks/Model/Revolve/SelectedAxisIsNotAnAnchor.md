# A selected revolve construction axis is not a sketch anchor

A vertical construction line selected by a revolved boss can look fixed to the sketch origin. Its saved coordinates and permanent-mark field do not establish a solver constraint.

The three disclosed ordinary SOLIDWORKS 2026 sources contain exactly four horizontal/vertical relations on the rectangular perimeter, with no relation on the actual selected axis and no origin coincidence or axis value driver. `moCompSketchEntHandle_c.f100` equals the selected line's permanent mark, separately from array index, line creation ID and COM segment ID. Treating that mark as a fixed-state flag or selecting a line by matching coordinates invents design intent.

Follow the actual feature wrapper, local component/profile identity and `sgLineHandle` into the owned line array. Preserve its true construction bit, endpoints and real relation references. Keep the axis unfixed unless actual native solver records prove an anchor. Derive positive angular value and reversal independently from their actual end/feature owners. The old native source observer did not measure sketch solver-status numbers, so record that separately from the exact relation census.

[Typed ownership and controlled process evidence](../../../../../../re/solidworks/records/OrdinaryRevolveSemanticOwnership2026.md).
