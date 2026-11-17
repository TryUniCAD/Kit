# External reference ids are not list counts

The header can load external-object records with preassigned ids. The
ordinary list constructor starts its high-water mark at -1.
`setExtObjToIndex` gives an unassigned record the next id; it retains an
existing id and raises the mark when that id is higher. Thus a fresh list
starts at zero and a list loaded with gaps can have a higher last id than
its entry count suggests.

Allocate from the high-water mark and derive the archive's direct slots
from the actual header reference entries. Keep the two quantities
separate. The [native record](../../../../../re/solidworks/records/AssemblyConstruction2026.md#ordinary-external-file-identity-in-the-header)
gives the constructor and setter addresses; REA evidence
`ev_be8687bb18958b4bada1f3ceee5bd90b8a2f1fc8b18489624d008c23315c7d15`
captures the setter control flow.
