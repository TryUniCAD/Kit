# Standalone SDK host destination and neutral self locator

Task `B04-SW2026-CONSTRUCTION`, owner `/root/flag_ownership`, delivery PR #121.
This is a separate continuation after the exact internal bridge tranche committed
at `f7ddea40bc2ce699e41bf259ecda0fdb7ecb23b9`. It changes only internal path
preparation and dedicated process evidence. The normal SOLIDWORKS adapter remains
read-only and unregistered for writing. No original held-out input, VM operation,
native executable analysis, public reader or part constructor is touched.

## Native evidence and limits

The oracle owner measured the previously generated Alpha and Beta parts from
different UNC destinations with their exact neutral basenames. The immutable
[relocation receipt](../measurements/2026/SdkPartRelocation01.json), SHA-256
`a2826d45fe5f278fd2ae45e862cfb744e4eef51fd3d304a688a9a2f8bd7a2362`,
binds eight fresh native processes and 220 numerical comparisons under SOLIDWORKS
2026 SP05.2, build `34.5.2.0604`. Both designs passed ordinary open, driving-depth
edit/rebuild, save and separate fresh reopen with healthy control brackets.

Alpha's archived `C:\KitSdkCandidates\sdk plain alpha.SLDPRT` existed, so that
case alone did not exclude resolution through the old locator. Beta's different
geometry and Unicode basename retained
`C:\KitSdkCandidates\sdk 部品 plain beta extended.SLDPRT`, explicitly verified
absent before and after all four phases. Its 110 numerical checks, clean load
status and persistent depth edit establish the selected standalone absent-locator
case. No held-out files were opened. The receipt is standalone-only and leaves
public writing disabled.

This evidence does not show that an assembly occurrence, drawing child reference
or arbitrary external dependency can ignore its path. It also does not prove
that the self record may be omitted, that any alternative placeholder namespace
works, or that a host directory corresponds to a real C: drive. Those are different
rules and remain outside this extension.

## Computed selection rule

[`SelectPartSelf`](../../../src/convert/adapters/solidworks/Core/Preparation/SelectPartSelf.py)
separates the requested output location from a standalone model's native self
locator. Its inputs are the selected final path, actual neutral model name and
the existing explicit `SelfFileInput` recipe. It performs no filesystem query or
file read.

| Input / owner               | Classification and rule                                                                                                                                                                               |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Actual final target         | Authored ordinary destination or existing `WriteOptions.values["final_destination"]`. Staging retains the actual caller location; no target is written by preparation.                                |
| Windows or UNC final target | Preserve the previous path rule and exact emitted bytes. The actual final native path, not a staging path, supplies self identity.                                                                    |
| POSIX final target          | Require an absolute ordinary path and exact neutral stem, with part suffix. Reject relative segments and implicit rename/case changes.                                                                |
| Authored recipe locator     | Its parent must be exactly the independently authored, measured `C:\KitSdkCandidates` namespace and its stem must match the actual neutral model. Assembly/drawing locators and other parents reject. |
| Selected native locator     | Join that explicit recipe parent with the actual requested host basename, preserving the basename and extension text. Native path validation must leave it one filename.                              |
| Native save event           | Retain the explicit recipe epoch. Do not infer it from filesystem modification time.                                                                                                                  |
| Container and graph fields  | Reuse the unchanged complete SDK composer. No serialized field, offset or stream is patched.                                                                                                          |

The namespace is a declared Kit construction policy and caller input, not a
vendor format constant or a value copied from a saved file. The emitted parent
comes from the actual typed recipe; the literal restricts admission to the measured
policy. The basename is computed from the final target and checked against the
neutral model. This rule claims no host-to-Windows drive mapping.

The exact existing one-part profile still governs the whole document: one active
configuration, one canonical rectangle support/profile, one driving length and
one plain forward blind create body. Assemblies, drawings, extra bodies or
configurations, external selections, unsupported provenance/payloads and unknown
linked/bundle options reject. Unnamed binary streams still reject. Named binary
preparation needs the same explicit final identity and does not write the sink.

Linked drawing and assembly builders continue using their actual qualified child
identity construction. They must not substitute this standalone neutral locator
for a dependency path. See the [specific distinction](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Construction/StandaloneSelfLocatorsAreNotChildReferences.md).

## Source and process proof

The eight-path executable overlay has SHA-256
`b9c4a30219228d3a54a904ef7fb07284b056483228584477e036dc026d9c0928`.
It owns three SDK path/preparation modules, two research transports and three
permanent host-flow modules. The new policy changes no part/Config/CMgr/Resolved
layout or writer registration.

`TestPartHost` sends two independently authored neutral parts through separate
guarded processes. Each compares every stream and complete container with the
unchanged explicit Windows-locator candidate. Direct POSIX, staged POSIX, binary
and Windows routes must agree, with zero sink mutation and runtime input reads.
Thirteen invalid requests per design cover unmeasured locator parents, wrong
basename/type, renames, relative paths, unbound streams, linked/bundle options,
additional bodies/configurations and external support attempts.

`TestPartBridge` is required alongside the new process. Its Windows behavior,
public readback and intentional public save rejection remain covered. Its former
same-basename `/tmp` rejection is intentionally now supported; that one negative
becomes an unproved locator-parent rejection. Its remaining twenty-one-case
count and read guard are preserved. This is an explicit scope expansion, not a
weakened check or a passing result borrowed from the old snapshot.

Scoped Black, Ruff, strict Mypy, Pyright and steering checks passed for thirteen
normal source modules; AST parsing passed all eight owned executable paths. The
worker executed no product/schema/test code and used no VM. The root independently
froze 4,643 sources at base `a1dabeb81a9bbe1139ea5242e86720bdc58c8b50`, manifest
SHA-256 `aeba0d7f57d85616d2b5ecfe2e40dcb4d996b999ba4f676aa73516764e4ed386`,
and passed both permanent integrations. Its retained four-worker replay has
SHA-256 `11ba5f21b33791fcf011316956f784b76fa7383b1aea7798dd40f90edee1e7fd`.

Both previous bridge variants retained their exact complete container and all ten
stream hashes. The two new host variants passed direct/staged/binary/Windows
comparisons, exact basename checks and zero sink mutation. All sixty-eight invalid
requests rejected, with zero runtime input reads or SDK research implementation
imports across all four workers. Host container lengths are 8,177 and 8,259 bytes,
SHA-256 respectively
`15e83250b66d2484ae817a184d8d32eedf72538ee0a5c53743bc3fdbb18476d2` and
`8e8aedad649d719f42dbb1bc199cb5a8f72c86729cbe94abdd6c0b7be5064a1f`.
These are observations, not encoded size constants. The original bridge still
recovers the actual boss/profile/D1 through the public reader and rejects public
save without modifying the destination.

The worker independently checked every owned source binding and raw
request/stdout/stderr/stream report hash against that exact snapshot. The sanitized
[process receipt](../measurements/2026/SdkStandaloneHostPreparation01.json) binds
the complete outcomes and the separately owned native relocation evidence. The
raw proof does not record the Python version; the receipt does not infer it.
No new host-variant native or held-out acceptance is transferred from this process
proof, and public writer qualification remains false.

The CAD stopping conditions remain:

> The first is success under every criterion on this page.
> The second is the end of the available context.

The native relocation receipt supports this narrow standalone policy. It does not
complete held-out generalization, linked-document paths, the default presentation
policy or public writer admission.
