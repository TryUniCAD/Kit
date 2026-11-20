# Fusion verification needs a startup add-in

## Expectation

An installed Fusion application appears sufficient for a Python command to call the Fusion API directly.

## Actual behavior

The Fusion API executes inside Fusion.
A background worker must schedule API work on the application's main thread.
Firing a custom event does not prove that its handler ran.
See the [Application.fireCustomEvent contract](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Application_fireCustomEvent.htm).

An existing desktop process also fails the fresh-process requirement for candidate acceptance.
Launching another executable can redirect to that existing process.
An executable path or a successful launch therefore does not establish native verification.

## Workaround

Install KitVerify with `kit research --root CHECKOUT api enable fusion`.
Enable the add-in and **Run on Startup** inside Fusion, then close Fusion.
The verifier binds each request to the newly launched process PID, a nonce, a deadline, and the source hash.
The main-thread handler returns measurements before requesting shutdown of its own empty application process.
Missing replies, process redirection, and retained documents leave verification incomplete.

See [automatic native verification](../../../../Changes/Research/Automation/AutomaticNativeReaderVerification.md).
This behavior was identified through API documentation and source inspection.
Live startup and shutdown behavior remains unverified.
