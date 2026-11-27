# Test and scanner lane contention

## Expectation

Increasing matrix fanout makes candidates execute concurrently.

## Actual behavior

Shared job concurrency keys serialize unrelated candidates even when GitHub has spare runners. In [PR 279’s candidate](https://github.com/TryUniCAD/Kit/actions/runs/45365569812), shard 3 waited 18 minutes 47 seconds after planning before its 7 minute 33 second execution. Four lane sets still serialize a fifth candidate and PR lanes still serialize independent PRs.

## Workaround

[Enterprise hosted concurrency](../../../Changes/Ci/Scheduling/EnterpriseLaneSets.md) removes shared job lanes and matrix throttles. GitHub enforces 500 total standard jobs, including at most 50 macOS jobs. All events and repositories share the allowance; a hundred admitted candidates can still wait for capacity. Keep workflow-level candidate isolation, obsolete-run cleanup, paced API polling and every acceptance gate. Activate the desired manifest separately after rollout and measure scheduling latency; configuration alone proves no throughput improvement or guarantee against stalls.
