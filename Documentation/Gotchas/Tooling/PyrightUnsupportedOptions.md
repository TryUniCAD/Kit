# Pinned Pyright reports unsupported configuration options

## Expectation

The pinned `pyright==1.1.414` accepts every setting in the repository configuration.

## Actual behavior

The targeted native extent check completed with zero code diagnostics, but its standard error reported three unrecognized configuration settings: `reportImplicitAbstractClass`, `reportIncompleteStubValue`, and `reportUnsafeMultipleInheritance`. This observation does not mean those requested checks ran.

## Workaround

Retain the configuration notices separately from the code diagnostic count. Use the existing remote quality gates for repository acceptance. Do not describe a zero-error targeted report as evidence that unsupported options were enforced.

The extent investigation records its tool version and notices in `re/Fusion/Reconstruction/CircularSpans/Validation.json`.
