# Rebuild policy read can send UI notifications

**Expectation:** `uiEnvironment::getAskRegen(true)` is a pure read of one rebuild preference.

**Actual behavior:** exact 2026 code first checks a separate cached registry word, then queries the real `MSG_NEEDS_UPDATE_ON_OPEN` dont-ask option. The option's boolean notification path may synchronously send window message `0x8160` with the actual option name. A matching original message-map handler records a unique name and invalidates/updates a window. Its actual live receiver remains conditional in this source checkpoint.

**Workaround:** distinguish the cached gate, selected option value and notification path. Observe existing operands when diagnosing the native caller; do not invoke the getter merely to inspect it, change a setting, or assume debugger/timing independence from the top-level getter body. The measured part configuration error-128 producer has no call to this getter, so the separate policy path cannot substitute for its actual decision. [Exact source and remaining boundaries](../../../../../../re/solidworks/records/PartRebuildWarning2026.md)
