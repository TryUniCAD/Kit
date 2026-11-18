# Conversion engine and write boundaries

## Purpose

This reference explains conversion options, capability checks, and destination behavior.
Use the public [API reference](../Overview/ApiReference.md) for callable signatures.

## Read and write sequence

1. The API constructs reader options and writer options.
2. The engine selects a reader and obtains a `CadDocument`.
3. The registry selects a writer for the destination.
4. The writer produces staged output and a `WriteResult`.
5. The registry checks transfers and output policy.
6. The staging layer writes the accepted output to the destination.

These are implementation stages, not instructions to invoke internal functions.

## Independent policies

| Policy            | Public option                          | Scope                                 |
| ----------------- | -------------------------------------- | ------------------------------------- |
| Reader validation | `strict`                               | Input interpretation and validation   |
| Data selection    | `include_brep`, `include_tessellation` | Information requested from the reader |
| Model validation  | `validate` on `write_document`         | Neutral document validation           |
| Replacement       | `overwrite`                            | Existing destination handling         |
| Output usability  | `allow_carrier`                        | Result acceptance in the registry     |

`convert` constructs writer options with validation enabled.
`write_document` exposes `validate=True` as a separate option.
Adapter-specific values use `write_values` on `convert` and `values` on `write_document`.

## Capability accounting

The registry compares reported transfers with source capabilities.
Reported dropped capabilities cause a capability-loss error.
Transfer records must account for the source capability set.
The registry can normalize unsupported usability claims for carrier-only output.

The default public API permits carriers.
The registry still requires self-contained output by default.
`allow_carrier=False` adds usability and blocker checks.
The implementation distinguishes `target_unsupported` from `writer_unimplemented` and `source_opaque`.
Do not describe this option as a universal ban on every carrier transfer.

## Path destinations

The path writer creates temporary storage beside the final destination.
The adapter writes into that storage.
The registry checks the result before output commitment.
The commit includes the requested file and any staged companion outputs.

With `overwrite=False`, a conflict in the destination set raises
`FileExistsError`. File publication also checks exclusivity in the filesystem
operation, so a file created by another process after the initial scan
retains its data. On a handled failure, rollback removes outputs that still
belong to the current write. With replacement enabled, the registry records
each backup as it moves the original and restores earlier backups if a later
move fails.

Multi-file commitment uses a sequence of filesystem operations. Keep
independent backups for recovery from power loss or external filesystem
changes.

## Stream destinations

The stream writer first writes to an in-memory staging stream.
The policy check runs before the caller's stream receives data.
The final write checks the count when `write()` returns a value other than `None`.
A returned count that differs from the payload length raises `OSError`.
The caller's stream can already contain partial data at that point.
If `write()` returns `None`, the count check does not run.
Successful return does not prove complete output for that stream.

Use a stream that reports an accurate count, or verify the written content independently.
Use a fresh stream after an unsuccessful final write.
Do not infer filesystem rollback behavior for an arbitrary stream.

## Replay and reconstruction

An adapter can replay the source document's own native data when its checks permit that path.
An edited document can require reconstruction or carrier representation.
A compatibility label reports the selected path.
It does not establish that an independent application accepted the output.

## Sources

- [API option construction](../../../src/convert/api/ApiConvert.py)
- [Output policy](../../../src/convert/adapters/base/WritePolicy.py)
- [Path staging](../../../src/convert/adapters/Staging/PathStaging.py)
- [Stream staging](../../../src/convert/adapters/Staging/StreamStaging.py)
- [Result evaluation](../../Tasks/InspectResult.md)
