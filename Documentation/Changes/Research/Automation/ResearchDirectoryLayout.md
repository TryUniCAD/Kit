# Focused research documentation and census paths

Four automation change entries now live in `Documentation/Changes/Research/Automation/`.
Their relative links and live consumers follow the new locations.
The [historical scope record](AutomationOnlyScope.md), [CI integration](AutomationOnlyCi.md), [capture binding](CaptureHistoryBinding.md) and [decoding requirement](MandatoryDecodingAutomation.md) retain their original evidence and limitations.

The Fusion census helper now lives at `tests/Research/Census/CollectFusion.py`.
Its repository-root lookup accounts for the additional directory, and the existing corpus test imports the defining module directly.
No collected test path, test function, assertion, workflow selector, decoder source or immutable evidence pin changes.
All fifteen restored phase commits remain in the candidate history.

The [failed path-policy job](https://github.com/TryUniCAD/Kit/actions/runs/44059460212/job/133957473058) counted 36 direct research change entries and 33 direct research test files.
Both directories exceeded the existing 32-file limit.
The focused moves reduce both direct counts to 32 without changing the policy or its exceptions.

Verification uses static formatting, syntax, typing, path, rationale and link checks.
No tests, collection, SDK, reader, generator or native application runs execute locally.
The repaired candidate still requires its own hosted checks and the existing acceptance evidence.
