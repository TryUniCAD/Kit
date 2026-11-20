# Mandatory research automation for decoding challenges

[Agent guidance](../../../../AGENTS.md) now requires agents to use the research automation pipeline for supported capture, deterministic comparison, inference and evidence tracking during decoding challenges.

Agents investigate unresolved findings and implement decoder rules from recorded evidence. They validate changes with deterministic checks and explicitly report missing automation capabilities. A detected pattern remains a hypothesis until its rule is proven; this requirement does not replace the reverse-engineering method or CAD acceptance criteria.

Use the [automation step register](../../../Reference/Research/AutomationSteps.md), [controller guide](../../../Reference/Research/ResearchController.md) and [deterministic inference guide](../Controller/DeterministicInference.md) for the available operations and current limits. Native decoder and writer follow-ups remain separate from this automation-only PR.

Verification is a source comparison against the user's supplied wording, Markdown formatting, link resolution and repository path/whitespace checks. This documentation change executes no tests, pipeline jobs, SDK or native applications and establishes no new decoding or native acceptance evidence.
