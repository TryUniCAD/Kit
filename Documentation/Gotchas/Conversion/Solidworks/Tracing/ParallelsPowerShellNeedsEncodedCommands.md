# Preserve PowerShell quoting through Parallels

## Expected

A shell-quoted PowerShell script reaches the guest with its nested string quotes intact.

## Observed

A read-only process inventory through `prlctl exec` lost nested double quotes before PowerShell parsed the script.
The resulting process-name array failed with a missing-argument parser error.
The VM remained running, and no CAD or licensing operation was issued.
Shell quoting alone did not preserve the script across this guest command boundary.

## Workaround

Encode the complete PowerShell script as UTF-16LE, then Base64.
Pass the ASCII value with PowerShell's `-EncodedCommand` option through the existing current-user transport.
Keep native executable paths and arguments separate when constructing the host process invocation.
The subsequent read-only inventory exited zero and returned the existing license-server processes with no SOLIDWORKS process present.

The [argument-order gotcha](../ParallelsCurrentUser.md) separately requires the VM name before `--current-user`.
Production conversion must not use the vendor application or this transport.
