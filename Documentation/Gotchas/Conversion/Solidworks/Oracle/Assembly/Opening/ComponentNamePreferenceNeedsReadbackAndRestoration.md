# Component-name preference needs read-back and restoration

The exact 2026 `ISldWorks.SetUserPreferenceToggle` contract returns `VT_VOID`, not a success Boolean. Python `None` is expected. Treating it as false would reject a setting that may already have changed.

For the authorized custom-name source control, read the actual original enum-18 value and durably record it before mutation. Record the restoration obligation before calling the setter. Validate the requested state through `GetUserPreferenceToggle`, then restore the actual original value in `finally` and verify that read-back before closing the owned application. Keep the fresh reopen under the original setting as the primary persistence test.

If the author process dies, use only the exact durable original-value capture. The separate recovery command first requires an idle oracle and creates its own verified application; it never attaches to or closes a foreign process and never guesses the original value. A restored preference is a cleanup fact, not native source or writer acceptance.

[Protocol and exact registered metadata](../../../../../../../re/solidworks/records/CustomComponentNamePreferenceRetry2026.md)
