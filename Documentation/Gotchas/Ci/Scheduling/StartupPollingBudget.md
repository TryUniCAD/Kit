# Removing startup idle does not start polling early

## Expectation

Removing the eight-minute commit-age floor should let queue aggregation detect early failures.

## Actual behavior

The first delay also uses a conservative charged fraction of one before any conditional polls exist.
With 100 sharing candidates, 1,000 remaining requests and one hour until reset, that delay is 720 seconds.
Deleting only the eight-minute floor therefore preserves a twelve-minute blind window.

## Workaround

Seed the conditional poll ETag from the existing startup workflow listing.
Treat that fixed startup inventory separately from recurring charged polls.
Start with the 30-second minimum when a seed exists, then retain the existing observed charged-fraction pacing.
Never cap mandatory budget or rate-limit waits to promise unconditional low latency.

The [early polling change](../../../Changes/Ci/Scheduling/QueueEarlyPolling.md) records the arithmetic and process evidence.
[PR #385](https://github.com/TryUniCAD/Kit/pull/385) addresses failed jobs within unfinished runs separately.
