# Popen waits when leaving its context

A timed `Popen.wait` inside a context can raise `TimeoutExpired` while the
child is still alive. On ordinary context exit, Python waits for the child
again without taking the timeout from the earlier call.
[Python subprocess documentation](https://docs.python.org/3.11/library/subprocess.html#popen-objects)

The Windows calibration identity fixture uses an explicit child lifetime.
It closes the pipe, waits for the normal ten-second deadline, and terminates
the child with a second bounded wait if the normal deadline expires. The
deadline failure still fails the test.
[Review finding](https://github.com/TryUniCAD/Kit/pull/210#discussion_r4649650707) ·
[Fixture](../../../../tests/Research/Windows/Calibration/CalIdentityTests.py)
