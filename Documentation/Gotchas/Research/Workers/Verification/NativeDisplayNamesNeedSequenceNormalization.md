# Native display names need sequence normalization

The SOLIDWORKS observation helper returned the correct one-element display-state sequence as a tuple. The first named-candidate observer compared it with a Python list, which caused the evidence gate to stop before applying D1. Both observed native processes opened and exited normally.

Normalize the sequence container on both sides and compare the strings and order exactly. Keep the stopped attempt separate. Recheck the matched input archive hash and configuration name before editing, since both generated `On` roles can pass geometry checks while having different names. The corrected observer qualified the `Default`-named input in fresh control, edit, reopen and trailing-control processes. [Exact measured roles](../../../../../re/solidworks/records/VendorBlindBossCompositionResiduals.md#native-lifecycle-timing)
