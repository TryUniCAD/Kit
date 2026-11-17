# Hopper window selection needs an application process query

In the observed System Events session, querying a generic `process` with the
correct Hopper PID returned no windows. Querying `application process` with that
same PID returned the three accessible Hopper documents. Core Graphics also
retained window records after the corresponding accessible document closed.

Select an `application process` by PID and verify its accessible window title.
When two documents have the same visible title, first identify the owned
document through Hopper's scripting API. Give that document a unique saved
database path before further window actions. Leave other documents alone.

The [constructor receipt](../../../../../re/solidworks/measurements/2026/MarkupHopperAnalysis01.json)
records the successful query on the uniquely named saved document.
