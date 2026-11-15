# Why the kernel read has never succeeded

## Behaviour

No writer behaviour changed. This records the exact state of the reverse-engineering provider, so
the one manual step that would unblock the class table is unambiguous.

## What was measured

`pskernel.dll` was copied out of the NX 2506 installation inside the virtual machine to
`re/nx/oracle/pskernel.dll` (72,362,496 bytes), so the blocker is provably not file location.

Session state, from `binary_session`:

```text
open             false
cleanup_pending  true
```

Every open is then refused, for every provider:

```text
provider hopper              cleanup_incomplete
provider ghidra              cleanup_incomplete
provider jeb                 cleanup_incomplete
provider rea-artifact-graph  cleanup_incomplete
```

with the same detail: `authenticated shutdown acknowledgement was not observed`, and a retained
runtime root under `/tmp/rea-*`.

The non-provider path is unavailable for this target as well:

```text
inspect_binary_layout -> capability_unavailable
  provider_id  pwntools-elf
  reason       the initial real-verified pwntools artifact profile supports Linux x64 only
```

`pskernel.dll` is a Windows PE, so the only provider that could read it is one of the analysis
providers, and all of them are blocked by the pending cleanup.

## The manual step

The provider's own remediation is to export any evidence, then restart the MCP connection:
close the retained document in Hopper (or let it finish analysis), and restart the REA/Hopper
bridge so a fresh authenticated session is established. Until that happens every target is
refused before analysis begins, which is why this work has no REA output at all.

## Limits

- This is an environment finding, not a format finding.
- The class table remains underived and `Writer.py` still requires a retained native document.
