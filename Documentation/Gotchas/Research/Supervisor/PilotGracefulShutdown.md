# Pilot owner recovery

The pilot smoke driver checks that the replacement supervisor recovers an active claim. The supervisor handles SIGTERM by requesting an orderly shutdown. A short worker can finish before that shutdown, leaving one completed attempt. The hosted smoke run observed exactly this outcome. [Hosted test report](https://github.com/TryUniCAD/Kit/actions/runs/44748039246)

For the active-recovery check, hold a live worker on POSIX, verify the controller still reports its claim as running, and terminate the identified supervisor abruptly. The replacement must record another attempt and complete that same job. The idle-restart check still uses ordinary termination.
