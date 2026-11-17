# Trace the drawing properties save boundary

The SOLIDWORKS 2026 observer samples the instruction after native
document properties save at `doccplu.dll+0x1df5b`, followed by the
third-party dispatch at `+0x1dfb5`. It retains the original owned
process and save-thread checks and uses one software breakpoint
at a time.

The cleanup path reselects the captured debugger process and
verifies its operating-system identity before explicit removal.
It separately compares each original guest-module instruction
byte before arming and after detach. Results record explicit
removal, measured byte restoration and debugger absence separately.
Published reports retain only lengths, hashes and status values.

Run `InspectBlankDrawingSaveAggregateSoftwarePropertiesMatched.py
Trial.json --packet-sha256 HASH --verify-only` to verify the frozen
source chain and inputs. Run it without `--verify-only` in the
pinned AMD64 oracle. The reduced-native lane must reach both
stops and save and reopen cleanly before the generated comparison.
Both pristine controls must pass. Native results are pending.
[Properties observer](../../../../../re/tooling/sw2026/drawing_properties_gate/InspectBlankDrawingSaveAggregateSoftwarePropertiesMatched.py) · [Debugger and restoration checks](../../../../../re/tooling/sw2026/drawing_properties_gate/DrawingSavePropertiesGateDbgEng.py) · [Prior cleanup finding](../../../../Gotchas/Conversion/Solidworks/Oracle/Drawings/DebuggerContextCanDisappearAfterSave.md)
