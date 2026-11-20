# Steering License Notices

The whole-file steering checker and the changed-comment rationale gate now recognize the exact complete leading seven-line PolyForm Strict SPDX notice retained by the repository. The domain recognizer lives in `tools/Steering/LicenseNotice.py`; both policies use its accepted comment positions rather than allowing arbitrary SPDX prefixes.

No configuration or baseline change is required. `python -m tools.Steering.SteeringCompliance` and direct execution of `tools/Steering/SteeringCompliance.py` retain the same arguments. The direct entry point locates its repository import root from its own file, so its caller does not need to run from the repository directory.

Only the complete unchanged notice starting at the first source line receives this exception. Altered, incomplete, misplaced, duplicated, inline, or unrelated comments remain subject to existing comment rules. Declarations still require their own valid rationale; a legal notice cannot replace it. Existing pragma and unchanged-comment behavior is preserved.

`tests/Steering/LicenseNoticeTests.py` authors the notice independently and exercises both checker entry forms plus the rationale CLI against real Git revisions. It covers the accepted notice, altered and incomplete text, misplaced and duplicated notices, ordinary leading and following comments, inline text, and missing rationale. These are process policy checks, not direct recognizer tests.

Verification is limited to source review and static formatting, typing, syntax, and repository policy checks. The process cases were not executed locally; hosted execution remains required.
