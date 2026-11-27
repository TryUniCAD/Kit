# SOLIDWORKS saved open-shell archive

The 2026 archive reader can decode the manager, configuration and resolved
feature records of the disclosed single inward open-shell profile. The saved
variant uses the actual linked body manager, stock chooser and rollback
reference, the shell's separated cap and auxiliary edge references, and its
live thickness dimension. The normal archive contexts retain their previous
class and layout guards.

The native controls are the initial save and the driving-thickness edit saved
by SOLIDWORKS 2026 SP05.2 (34.5.2.0604). The
[typed replay receipt](../../../../re/solidworks/measurements/2026/OpenShellTypedReplay01.json)
records six identical uncompressed stream re-emissions. Run
[ReplaySavedShell.py](../../../../re/tooling/sw2026/shell_source/ReplaySavedShell.py)
with the disclosed directory and a new output path. The audit reads the
hash-pinned controls and emits a numerical report. It establishes the archive
layout needed for C9 and C11 of the [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md)
and follows the [reverse-engineering playbook](../../../../re/Playbook/README.md).

This archive prerequisite carries no generated-output or held-out qualification.
The fixture observer and its native phase lock are independently pinned in
[OpenShellSourceLock2026](https://github.com/TryUniCAD/Kit/blob/84d925a36c79c2b3124aba3ac06830c95297bca1/re/solidworks/records/OpenShellSourceLock2026.md).

The resolved archive reader and writer reject requests that select both the
shell and chamfer layouts. The archive construction path supports one terminal
feature; a mixed-feature grammar is not qualified. The offline shell archive
build passed after this change.
