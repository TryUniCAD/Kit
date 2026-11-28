# A phase selector adds a serial runner pickup

Expected: a short phase-selector job adds only its twenty-second execution time before Pyright.
Actual: both the selector and its dependent check must obtain separate hosted runners.
On PR #368, those waits were 139 and 277 seconds respectively.
Pyright itself ran for 102 seconds, including 69 seconds of strict checking.

Run the same trusted-base phase selector as a step in each admitted light-check job.
Keep the old preflight contexts independently required for base-reporter compatibility.
Use job-level event conditions for PR-only checks so candidates request no extra deferred runners.
Preserve the base-SHA lookup and rejection of malformed markers or API errors.
See [inline PR phase selection](../../../Changes/Ci/Scheduling/InlinePrPhaseSelection.md).
