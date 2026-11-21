# Fusion startup must gate research imports

An add-in configured to run on startup also loads in ordinary Fusion sessions.
Enabling startup alone does not identify a session owned by the research verifier.

KitVerify now checks the documented `IsApplicationStartup` context before importing the selected research checkout.
An ordinary startup returns immediately.
An explicit manual run records readiness without registering a worker.
Only a fresh process launched by Kit receives the private session nonce that enables the main-thread handler and polling thread.
The handler additionally checks that each request has the same nonce and process ID.

See Autodesk's [script and add-in lifecycle reference](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm).
The behavior was checked against source and the API contract; licensed startup execution remains unavailable.
