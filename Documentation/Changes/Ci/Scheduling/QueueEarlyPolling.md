# Queue polling from startup

## Behavior

`CI Agg` no longer waits until eight minutes after the candidate commit before polling.
The startup workflow listing supplies the first page's `ETag` through Octokit's pagination response mapper.
Every subsequent workflow poll sends that value in `If-None-Match`, starting after 30 seconds.
There is no additional unconditional startup poll.
The existing startup inventory still reads workflow runs and checks, with pagination when necessary.

Startup reads are fixed costs, not recurring charged polls.
Before observing a recurring poll, a seeded ETag allows the 30-second minimum interval.
Afterward, the existing charged-poll ratio controls pacing.
Unchanged authenticated `304` responses [cost no primary requests](https://docs.github.com/en/rest/guides/best-practices-for-using-the-rest-api#use-conditional-requests).
They do not trigger another full inventory.
Changed responses still trigger a full inventory only under the existing workflow completion rules.

The 500-request reserve, 100-candidate sharing factor, rate-limit waits, and aggregation deadline remain unchanged.
So do check registration, failure rules, `CI Agg`, and `Merge queue acceptance`.
No workflow configuration or live ruleset changes are required.
The trusted reporter must reach `main` before new queue candidates use it.

## Rate budget

The repository job-token limit is 1,000 primary requests per hour.
At full remaining budget and an hour until reset, recurring charged polls have 500 requests above the reserve.
The unchanged interval is `3600 × 100 / (remaining − 500) × charged / polls`, with a 30-second minimum.

- At 25 concurrent candidates, unchanged polling produces `25 × 120 = 3000` conditional requests per hour and zero primary charges.
- At 100 candidates, it produces `100 × 120 = 12000` conditional requests per hour and zero primary charges.
- With every poll charged, the full-budget interval is 720 seconds: five charged polls per candidate per hour.
  That is 125 charges for 25 candidates, or 500 for 100 candidates, before fixed inventories and other jobs.
- With a charged fraction `f`, the full-budget interval is `max(30, 720f)` seconds.
  For example, `f = 1/24` reaches the 30-second floor at the same nominal charged rate.
- The normal unpaginated startup inventory costs two requests per candidate: 50 for 25 candidates, or 200 for 100 candidates.
  Three-request inventories cost 75 or 300 respectively.
  The change adds zero unconditional startup reads.
  Live remaining budget already includes these costs when the next wait is calculated.
- Changed responses remain charged, even with `If-None-Match`.
  Other jobs and final inventories also consume budget; their spend increases the calculated interval.
  At 500 remaining or less, polling waits until reset.

These are pacing calculations, not a hard reservation across independently running jobs.
Startup and changed responses can coincide, and secondary limits still apply to conditional requests.
Existing `403` and `429` handling waits for `Retry-After` or `x-ratelimit-reset`.

## Detection latency and complementary work

Previously, a failure just after startup waited at least eight minutes from commit creation.
At 1,000 remaining with one hour to reset, the 100-candidate brake actually delayed the first poll 12 minutes.
A failure at 60 seconds therefore waited roughly 11 more minutes under those conditions.

Now unchanged early polling checks every 30 seconds, including during the first eight minutes.
The process fixture detects a workflow failure at 60 seconds on the 60-second poll.
A failure immediately after a normal poll waits at most 30 seconds, excluding request execution and scheduling.
Budget exhaustion, changed responses, or server-directed waits can still extend that interval, potentially until reset.
An unconditional 60-second bound cannot coexist with the required budget brake at 100 concurrent changing candidates.

[PR #385](https://github.com/TryUniCAD/Kit/pull/385) separately reads jobs from unfinished workflow runs.
That change removes the workflow-completion detection blind spot; this change removes the startup timing blind spot.
This PR does not duplicate that job-reading implementation.
Without it, a failed job in an unfinished run still waits for workflow completion.
With both changes, early job failures become observable on the first applicable poll.
Its additional charged reads remain subject to the same budget constraints.

## Verification

The existing Node process fixture executes the real reporter with fake GitHub responses and a fake clock.
The Python process checks require conditional headers on the first and later polls.
They cover a failure at 60 seconds, free unchanged polls at 30 and 60 seconds, low-budget pacing, and exhaustion.
They retain primary-limit, secondary-limit, forbidden-response, success, and failure scenarios.
All 676 `tests/Policy` process checks passed locally in 51.63 seconds.
Prettier and Black checks passed for the modified files.
Current-head PR results are recorded in the delivery PR.
Live queue timing requires rollout; PR checks do not establish queue acceptance.
