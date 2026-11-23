# Windows supervisor CLI launcher

The installed `kit research --root CHECKOUT supervisor ...` command now admits Windows research checkouts.
The supervisor still requires Windows 10 or newer, Python 3.14 or newer, and the locked `pywin32` development extra.

Windows supervisor children use separate process groups.
For supervisor commands, the launcher forwards handled `SIGINT`, `SIGTERM`, and `SIGBREAK` as `CTRL_BREAK_EVENT`.
The supervisor accepts break events through its existing shutdown path.
The CLI inspects the selected supervisor's explicit Windows shutdown protocol before launching it.
Older or unsupported checkouts fail with an update instruction before any worker can claim a job.
The launcher polls its wait so Python can dispatch pending Windows signal handlers while the supervisor remains active.
It waits for cleanup and preserves the supervisor's exit status.
Other Windows research commands retain their existing wait-for-completion behavior.
Linux and macOS retain their existing signal and session handling.

Console events require a shared Windows console.
Forced launcher termination cannot be forwarded.
This change does not configure application workers, enable model advice, or establish CAD acceptance.

Use the existing [research command procedure](../../../../Tasks/ResearchCommandLine.md) with a trusted checkout and actual supervisor configuration.
The [cancellation gotcha](../../../../Gotchas/Research/WindowsCliCancellation.md) explains the platform boundary.

## Verification

Native process coverage under `tests/Research/Windows/Cli/LauncherTests.py` exercises all three handled signal types against the actual supervisor.
`NativeTests.py` sends actual console events through the installed executable in a private hidden console.
Each case requires a settlement receipt and termination of the independently recorded worker process tree.
Cancellation must finish within 15 seconds of the recorded request, before the safety deadline can settle workers independently.
Compatibility cases reject missing, unsupported, and invalid protocol markers without changing a queued controller job.
The same complete legacy fixture then dispatches that queued job directly, proving its dependencies are present.
Native break-event cases create an explicit launcher process group and target its recorded root identifier.
Private test job custody handles failed launchers and surviving descendants without masking successful worker-cleanup assertions.
These cases use the existing Windows merge-queue selection and completeness checks.
The existing CLI bridge compatibility check now requires supervisor help on Windows as well as POSIX systems.
Remote execution results remain pending until CI runs this revision.

The installed Windows CLI reached actual supervisor help with Python 3.14.6 and locked `pywin32` dependencies.
Focused Mypy 2.4.1 checks passed for seven changed files with both Windows and Linux targets.
The [conditional import gotcha](../../../../Gotchas/Research/PlatformConditionalImports.md) records the required platform guards.
