# SOLIDWORKS oracle diagnostics

The 2026 research harness now passes a Boolean reference to the feature-error
API and records its warning result. It previously passed the integer-reference
helper used by document open/save calls, producing type mismatches instead of
feature error evidence. Exceptions remain visible in measurement records.

The dialog observer now filters windows by SOLIDWORKS process identity before
clicking a dismissal button. Its process list no longer targets the system-wide
Windows error-reporting executable. The tasklist lookup fails explicitly instead
of falling back to all desktop dialogs.

`re/tooling/sw2026/InspectTypeLib.py <absolute-tlb-path> <interface> <method>`
records installed COM declarations, library identity and source hash without
launching or attaching to CAD. Its actual 2026 inspection recovered a pointer
to `VT_BOOL` for `IFeature.GetErrorCode2.IsWarning`. See the
[Boolean output gotcha](../../Gotchas/Conversion/Solidworks/FeatureErrorBooleanOutput.md)
and [descriptor](../../../re/solidworks/v2026/evidence/FeatureErrorTypeLibrary.json).

Actual evidence: the five source authoring operations saved successfully with
one solid body and no dismissed dialogs; the original feature error queries
were unavailable and remain labelled as such. The type-library inspection was
static. No tests ran locally, and no generated-output acceptance is claimed.

The [adapter guide](../../Reference/Adapters/Solidworks.md) remains read-only.
## Native progress windows

The fresh-file inspector exposed a watchdog interference: an untitled native
loading-progress window uses the dialog class and contains a Close control.
The watchdog now considers only visible, enabled buttons and preserves the
observed three-stage progress window without clicking it. These windows are
recorded separately in `progress_windows`; actual dismissed warnings and errors
still fail health checks. The contaminated batch is not accepted and requires
complete repetition. See the
[progress-window finding](../../Gotchas/Conversion/Solidworks/Tracing/ProgressWindowsAreNotWarnings.md).
