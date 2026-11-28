# A restricted PATH can select unavailable system Git

The real offline context smoke initially cleared its environment and set PATH to Python's platform default.
On this Mac that selected `/usr/bin/git`, which exited with the Xcode developer-tools installation error.
The repository's installed Git was available on the existing trusted PATH.

Preserve that PATH for Git orchestration while passing an explicit environment without authentication variables.
The trusted planning compiler uses an absolute Python executable, needs no Git process, and retains its stricter environment.
Do not solve executable discovery by inheriting account credentials or disabling process isolation.
