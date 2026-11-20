# Hybrid experiment planner decision

**Status:** Proposed design, not implemented by this PR.
**Date:** 2026-11-18.
**Audience:** Research controller and native worker maintainers.

## Context and current ownership

Use deterministic scheduling for required coverage and optional model advice for targeted experiments.
The controller validates every proposal and accepts results only through independent proof gates.

The programme already contains controller, inference and worker implementations.
This proposal extends that work instead of creating a second controller.
It does not claim that all planner components remain unimplemented.

At inspection, [PR #94](https://github.com/TryUniCAD/Kit/pull/94) was closed and superseded by
[PR #158](https://github.com/TryUniCAD/Kit/pull/158).
The inspected successor head was `0b66cc014bac58e5171585c926b0773a9cdd570e`.
Its [step register](https://github.com/TryUniCAD/Kit/blob/0b66cc014bac58e5171585c926b0773a9cdd570e/Documentation/Reference/Research/AutomationSteps.md)
records A03 as complete, A07 as blocked, A08 as active and optional A10 as planned.
These are source-register observations, not independent qualification of those implementations.
Refresh their state before claiming implementation work.

This separate PR owns the planning supplement only.
It does not transfer the programme's implementation ownership or replace its delivery rule.
The [build plan](BuildPlan.md) maps proposed work onto existing milestones.

## Decision

The deterministic controller owns family priorities, dependencies, coverage, resource reservations, execution, evidence and acceptance.
An optional model proposes experiments within an eligible family.
Each proposal identifies competing hypotheses and predicts different measurable observations for them.
The controller evaluates those predictions before authoring a sample.

Start with fixed controls, coverage grids and sealed validation samples.
Request advice when completed analysis leaves hypotheses that the scheduled samples cannot distinguish.
The model cannot waive coverage, modify a recipe, run arbitrary code or declare support.
The controller preserves the existing optional A10 escalation and failure-routing contracts.

Without a model provider, fixed planning and deterministic inference remain usable.
Unexplained work expands within configured bounds or parks with evidence.
Replay uses persisted decisions and responses without another model call.
New live model responses are not guaranteed to repeat.

## Options considered

| Option                               | Benefit                                   | Limitation                                           |
| ------------------------------------ | ----------------------------------------- | ---------------------------------------------------- |
| Fixed grids only                     | Predictable coverage and no model spend   | Large grids can produce weak contrasts               |
| Model controls all work              | Flexible experiment selection             | Variable decisions and difficult coverage accounting |
| Deterministic controller with advice | Auditable coverage and targeted contrasts | Requires prediction, validation and replay contracts |

Choose the hybrid and measure its benefit against fixed planning.
Count rejected proposals, model latency and parked tasks in that comparison.

## Boundaries

- Use only registered recipes, typed parameters and bounded combinations.
- Keep holdout observations outside model context and formula fitting.
- Evaluate formulas through registered functions or a bounded typed interpreter.
  Never execute generated Python, shell commands or arbitrary `eval`.
- Keep Fusion capture serial and respect existing capture holds and native lifecycle rules.
  Application loss or an uncertain transaction stops further capture.
- Keep native authoring and validation outside production conversion runtime.
- Distinguish completed research jobs from qualified format support.
  Apply all [CAD success criteria](../../Operations/CadSuccessCriteria.md).
- Commit verified generated changes only within authorized scope on a working branch.
  The planner itself does not publish branches, messages or PRs.

## Consequences and next action

Required coverage stays predictable while uncertain fields can receive targeted experiments.
Advice adds provider cost, rejection handling and evidence-isolation requirements.
Keep advice disabled by default until comparable experiments show a benefit.

Implement the [contracts](Contracts.md) through the [build milestones](BuildPlan.md).
Reuse accepted controller capabilities and retain unresolved acceptance requirements.
Planner completion does not establish complete native writing or lossless conversion.
