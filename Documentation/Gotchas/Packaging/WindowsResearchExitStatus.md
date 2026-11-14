# Windows research commands must wait for their child

A launcher using `os.execv` can appear to preserve the selected tool's lifetime and exit status on every platform.
The Windows execution model does not provide the POSIX process replacement contract expected by this launcher.
Returning before the research tool finishes can lose failure statuses consumed by scripts and CI.

On Windows, the CLI now uses [subprocess.run](https://docs.python.org/3.14/library/subprocess.html#subprocess.run), inherits terminal streams, waits for completion, and exits with the child's return code.
Linux and macOS retain process replacement for signal and supervisor ownership.
The supervisor itself still requires Linux or macOS.

Windows process coverage exercises pinned readers, artifact identity, failed batches, stale leases, and explicit supervisor refusal.
This behavior was identified during source review; accepted-head Windows execution evidence belongs to remote CI.
No local commands or decoding runs were used to reproduce it.
