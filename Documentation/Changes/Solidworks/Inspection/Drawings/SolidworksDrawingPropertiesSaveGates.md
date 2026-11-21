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
Both pristine controls must pass.

The native comparison passed with seven distinct processes and healthy
brackets. The reduced-native lane delivered both stops. The generated
save returned while the post-properties stop was armed and unobserved.
Explicit removal, restored original site bytes and final debugger
absence were verified in both traced lanes. The properties call entry
and its preceding setup require the next split.
[Properties observer](../../../../../re/tooling/sw2026/drawing_properties_gate/InspectBlankDrawingSaveAggregateSoftwarePropertiesMatched.py) · [Debugger and restoration checks](../../../../../re/tooling/sw2026/drawing_properties_gate/DrawingSavePropertiesGateDbgEng.py) · [Prior cleanup finding](../../../../Gotchas/Conversion/Solidworks/Oracle/Drawings/DebuggerContextCanDisappearAfterSave.md)
[Native properties comparison](../../../../../re/solidworks/measurements/2026/DrawingBlankSavePropertiesGateNative01.json)
