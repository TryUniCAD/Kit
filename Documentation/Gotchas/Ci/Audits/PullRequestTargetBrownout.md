# Trusted workflows can fail before creating jobs during a brownout

## Expectation

A failed trusted aggregate should expose a failed job or diagnostic through the workflow and check APIs.

## Observed behavior

On SOLIDWORKS PR 121, [aggregate run 43918632702](https://github.com/TryUniCAD/Kit/actions/runs/43918632702), for head `55d0912a36748e3c6b4829471b59dc9620c15b9a`, concluded `startup_failure`. Its job list and check-suite run count were both zero. Nine current-head `pull_request_target` workflows failed at startup while the ordinary PR workflows ran successfully. An earlier startup run also rejected a manual rerun as unsupported.

The rendered run page's annotation identified GitHub's scheduled default-policy brownout for affected public repositories. It stated that the window would end on 16 November 2026 at 18:00 UTC, or 10:00 Pacific. This observation identifies the current aggregate's startup cause; it does not prove that later runs will pass. The retrieved run-page HTML had SHA-256 `acd17df8b6044b6b12b519636fac5c6d8a44b60f4ebd14cd5bbb304fa684b9ac`. The raw page remains in external research scratch; no captured page or third-party script is shipped.

## Workaround

Inspect the run's rendered annotations when APIs return no jobs or actionable diagnostic. Keep successful component checks separate from overall aggregate health. After the stated window, obtain fresh applicable current-head trusted-workflow results through supported reruns or a legitimate new revision. Do not treat a calendar deadline as passing CI, repeatedly retry an unsupported run, weaken gates or change repository protections to conceal the failure. Continue independent authorized work while the external window remains active.

The [held-out prediction entry](../../../Changes/Solidworks/Inspection/Extrusions/SolidworksEndConditionHeldoutPrediction.md) records the successful component job and its separate readiness limits.
