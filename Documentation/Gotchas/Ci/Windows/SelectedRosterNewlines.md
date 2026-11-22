# Selected roster newlines

Python text output might appear byte-compatible with the roster produced by Bash.
On Windows, default text writes translate LF to CRLF.
The Linux artifact verifier then retains carriage returns inside selected test identifiers.
Passing pytest outcomes no longer match those identifiers, and byte-for-byte roster comparison fails.

Write selected rosters with `newline="\n"`.
The platform scheduling process checks LF output on Windows and macOS through the shared suite.
See [runtime scheduling](../../../Changes/Ci/QueueRuntimeScheduling.md).
