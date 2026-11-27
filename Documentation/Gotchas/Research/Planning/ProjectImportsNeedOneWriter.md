# Project imports require one writer

## Expectation

Interrupting an import stops all queued requests before another importer starts.

## Actual behavior

A Python thread pool can continue draining queued work while its owner handles an
interrupt. Overlapping task-owned importers created duplicate draft items for the
same stable scope IDs. A readback audit identified 408 duplicate groups.

## Workaround

Use the project-wide operating-system writer lease. Cancellation must cancel queued
futures and wait for active requests before releasing the lease. Reconcile remote
scope markers after an uncertain response before retrying creation.

The repair compares bodies against this task's recorded generated versions and
merges compatible fields while preserving recorded progress. Distinct manual content
or conflicting fields remain untouched and are reported for explicit resolution.
