# Retain the COM controller during native tracing

Expected behavior: an existing SOLIDWORKS process can be reacquired by
`GetActiveObject` after Frida hooks activate.

Observed behavior: the first 2026 loader capture attached to PID 8976 and
activated 20 hooks after verifying both module hashes. Its action then raised
COM error `-2147221021`, `Operation unavailable`. It captured only the hooks-ready
event, no archive reads. A visible process and successful native attachment did
not establish running-object-table availability.

The private capture is `.rescratch/sw26/tupni/ladder-L1-first.json`. The
[usage ledger](../../../../re/solidworks/records/Tupni2026.md) records its outcome.

Workaround: use the user's existing restart authorization, start the goal-owned
application through the committed controller, and retain that controller in the
same Python process through hook activation, the selected action and native
detach. Close the application only after tracing detaches. Keep the capture's
preparation hash and cleanup outcome. Never restart a shared session without
authorization, and never treat setup success as recovered format knowledge.
