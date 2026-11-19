# Retry blank rewrite observation with the qualified COM environment

The first canonical-blank rewrite batch completed four identical paired SDK builds, then both native controls failed before launch because isolated Python could not import `pythoncom`. The observer-only retry uses the previously qualified native environment and adds a passive observer import gate. SDK source and generation remain unchanged.

The retry binds the original failure, revalidates all four SDK reports and both retained output pairs, and observes the exact same candidate paths and bytes from a separate native-result root. No source metadata, layout, destination/save event, SDK result flag or public writer scope changes. All private data stays guest-local and the new export reports reused inputs and zero new SDK builds.

[Negative observation](../../../../../../re/solidworks/measurements/2026/BlankRewriteObserverIsolation01.json) · [Retry protocol](../../../../../../re/solidworks/records/BlankRewriteHeldoutObserverRetry2026.md) · [Import-environment gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/Rewrite/IsolatedPythonHidesUserSiteComObservers.md)
