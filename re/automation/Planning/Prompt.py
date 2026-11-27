import json


def task_prompt(item):
    return f'''use standard-pr-practice to investigate {item["Id"]}: {item["Name"]}

Refresh main, the live project claim, open PRs and {item["Source"]} before starting.
Do not start taken work or work whose required evidence is unavailable.
Claim the bounded task with owner, dependencies, branch, delivery PR and exit condition.
Use a fresh feat/ or fix/ branch and an isolated registered checkout.
Read AGENTS.md and Documentation/Planning/README.md.
For CAD work read Documentation/Reference/Operations/CadSuccessCriteria.md and re/Playbook/README.md in full and the relevant phase chapters.
Reuse existing deterministic research automation, CAD API workers and the research CLI.
Inspect existing evidence before choosing new contrasts and reserve independent holdouts.
Retain controls, failed attempts, documents, hashes, receipts and unresolved findings.
Prove rules on heldouts and counterexamples; no donor data or proprietary binaries.
Coordinate native host leases; model execution stays off unless separately authorized.
Keep capture, decode, semantics, writing and native acceptance separate.
Exit: {json.dumps(item["Exit"], ensure_ascii=False)}
Window: {item.get("Start")} to {item.get("Finish")} — investigation estimate only.
Update the project, owning register, planning links and generated views at each state change.
Deliver a scoped PR with exact tested revision evidence and address configured review.
Do not merge without explicit administrator authorization.'''
