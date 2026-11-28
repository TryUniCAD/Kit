# Thin-revolve fixture cleanup after a timed-out worker

A thin-revolve file-publication case uses a measured Windows path. When the worker acquires the root and is killed on timeout, its cleanup is lost. The next attempt sees an existing root and cannot distinguish it from a preserved native packet.

The supervising process acquires the directory exclusively before dispatching the timed child. It removes the directory only when the original file identity and unique marker still agree. An existing, moved or replaced root stays untouched. The timeout still fails the suite case so the retry starts independently. [Subprocess timeout semantics](https://docs.python.org/3.12/library/subprocess.html#subprocess.run) · [Windows path identity](https://docs.python.org/3.12/library/os.html#os.lstat) · [Guarded observations](../../../../re/solidworks/measurements/2026/SdkThinReadReviewRecovery01.json)
