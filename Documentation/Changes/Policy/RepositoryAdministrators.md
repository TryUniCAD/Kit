# Repository-policy administrators

## Behavior

`jdharcourt` and `odinglynn` are repository-policy administrators with merge privileges.
Either may explicitly authorize agent queue enrollment, auto-merge, or merging.
Agents must verify the requester's GitHub identity.
Other administrators must have verified current GitHub `admin` permission.

The [agent rules](../../../AGENTS.md) and [repository skill](../../../.agents/skills/standard-pr-practice/SKILL.md#administrator-requested-merges) define this authority.

## Limits

This designation does not grant GitHub platform permissions.
Current-head CI, configured review, queue acceptance, protections, and tool approvals remain required.
An implementation request alone does not authorize merging.

## Verification

The user identified their GitHub login as `jdharcourt` and requested this policy designation.
On 2026-11-26, `GET /repos/TryUniCAD/Kit/collaborators/jdharcourt/permission` returned `write` and `admin: false`.
The policy distinguishes workflow authority from platform access.
This documentation change does not exercise merge privileges or change GitHub settings.
