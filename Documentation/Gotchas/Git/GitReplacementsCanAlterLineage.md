# Git replacements can alter lineage and streamed content

## Expectation

An exact commit or blob SHA passed to Git might appear sufficient to identify immutable bytes.

## Actual behavior

Local replacement refs and grafts can change the objects or ancestry observed by Git. Inherited `GIT_DIR`, object-directory and configuration overrides can also redirect child commands despite `-C`. Hardening a single-command wrapper leaves an independent streaming `cat-file --batch` process exposed unless it receives the same policy.

## Workaround

The corpus and capture tools use `--no-replace-objects`, disable grafts and inherited Git overrides, suppress system/global configuration and disable lazy fetching for both single commands and streaming object reads. Explicit historical acquisition names the reviewed authority and allowed blobs. Process cases exercise replaced commits, grafts, streaming blob replacement and hostile child environments; hosted execution remains required. See [capture history binding](../../Changes/Research/CaptureHistoryBinding.md).
