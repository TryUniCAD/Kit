<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Preserve successful provider results during cleanup

The bounded builder provider launcher checks for live owned process-group members
before sending a termination signal. A successful exited provider no longer
becomes an invalid generation solely because macOS rejects a signal to its
zombie-only process group. The leader remains unreaped until descendant cleanup
is verified, preserving its identity throughout the check.

Live descendants still require termination. A signal permission race is accepted
only when a second independent inspection proves no live group members remain.
Inspection uncertainty, surviving descendants, signal failures and wait timeouts
remain infrastructure failures named `provider_cleanup_failed`. Existing builder
repair routing stops on that classification instead of spending another model
call. Windows job-object cleanup retains its ownership checks and uses the same
failure classification.

Four real process checks cover a normally exited provider, an exited provider
with a surviving child, a timed-out provider with a child, and an overflowing
provider log. Each requires verified termination and no live child. These checks
make no model calls and do not establish native CAD qualification. Windows and
Linux execution remain separate platform validation.

See the [macOS process-group gotcha](../../../../Gotchas/Research/Workers/Inference/ExitedProviderGroups.md).
