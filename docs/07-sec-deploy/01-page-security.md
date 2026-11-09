---
title: "Security Boundaries & Validation"
wiki_page_id: "page-security"
---

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [src/convert/Security/PathBoundary.py](src/convert/Security/PathBoundary.py)
- [src/convert/Security/ProgramBoundary.py](src/convert/Security/ProgramBoundary.py)
- [SECURITY.md](SECURITY.md)
- [src/convert/adapters/freecad/Archive.py](src/convert/adapters/freecad/Archive.py)
- [AGENTS.md](AGENTS.md)
- [tools/skills/Descriptions.py](tools/skills/Descriptions.py)
</details>

# Security Boundaries & Validation

Security boundaries and validation logic protect the Kit project by enforcing strict constraints on file system access, external program execution, and data integrity during CAD format conversion. These systems prevent path traversal attacks, execution of unauthorized binaries, and resource exhaustion from malformed archives.

The project defines security scope within `src/`, `tools/`, and `.github/` directories, while excluding vendor tooling and local CAD installations from the primary security perimeter. Automated monitoring via continuous integration ensures the supply chain and codebase remain free of secrets and known vulnerabilities.

Sources: [SECURITY.md:21-27](SECURITY.md#L21-L27), [tools/skills/Descriptions.py:34](tools/skills/Descriptions.py#L34)

## Path and Program Boundaries

The security system isolates file operations and program execution through dedicated boundary modules. These modules ensure that the application only interacts with verified paths and authorized external binaries.

### Path Resolution and Validation
The `PathBoundary` module provides functions to resolve and validate paths for inputs, temporary files, and labels. It prevents access outside of designated workspaces.
*  `ResolveInput`: Resolves and verifies paths for source CAD documents.
*  `ResolveTemp`: Manages the creation and resolution of temporary file paths for conversion artifacts.
*  `ValidateLabel`: Enforces naming conventions on labels to ensure they are safe for use as identifiers.

Sources: [src/convert/Security/PathBoundary.py](src/convert/Security/PathBoundary.py), [re/tooling/windbg/Multitrace.py:23](re/tooling/windbg/Multitrace.py#L23), [re/tooling/windbg/Show.py:18](re/tooling/windbg/Show.py#L18)

### External Program Isolation
The `ProgramBoundary` module identifies the location of authorized external tools, such as the FreeCAD oracle used for verification. Functions like `GetFreecadPath` ensure that the system executes only the intended version of external applications.

Sources: [src/convert/Security/ProgramBoundary.py](src/convert/Security/ProgramBoundary.py), [tests/convert/formats/RandomAssemblyTests.py:27](tests/convert/formats/RandomAssemblyTests.py#L27)

## Archive and Content Validation

The conversion adapters implement deep validation for proprietary and open CAD containers. The `Archive` module for FreeCAD (FCStd) serves as a primary example of enforcing safety limits on ZIP structures and XML content.

### Archive Security Gates
The system validates ZIP archive members before extraction to prevent "zip bomb" attacks and path traversal.

| Constraint | Limit / Logic | Purpose |
| :--- | :--- | :--- |
| `KMaxEntries` | 16,384 | Prevents resource exhaustion from excessive file counts. |
| `KMaxEntrySize` | 512 MB | Limits the size of any single file within an archive. |
| `KMaxTotalSize` | 1 GB | Limits the aggregate size of the processed archive. |
| `KMaxCompressionRatio` | 500 | Detects and rejects potential "zip bombs." |
| Encryption | Rejected | Rejects encrypted entries to ensure content inspectability. |
| Symbolic Links | Rejected | Prevents path traversal via link redirection. |

Sources: [src/convert/adapters/freecad/Archive.py:108-132](src/convert/adapters/freecad/Archive.py#L108-L132), [src/convert/adapters/freecad/Archive.py:155-179](src/convert/adapters/freecad/Archive.py#L155-L179)

### XML Validation
CAD metadata stored in XML format (e.g., `Document.xml`) is subject to node and depth limits to prevent parser exploits.

```mermaid
flowchart TD
    Start[XML Parsing] --> Parse[Parse Document.xml]
    Parse --> NodeCount{Node Count > 2M?}
    NodeCount -- Yes --> Fail[Raise ValueError]
    NodeCount -- No --> DepthCheck{Depth > 256?}
    DepthCheck -- Yes --> Fail
    DepthCheck -- No --> SchemaCheck{Schema Version < 2?}
    SchemaCheck -- Yes --> Fail
    SchemaCheck -- No --> Success[Return Validated Root]
```

The logic walks the XML tree, incrementing counters for nodes and tracking nesting depth. It requires a minimum schema version to ensure compatibility with modern security structures.

Sources: [src/convert/adapters/freecad/Archive.py:214-232](src/convert/adapters/freecad/Archive.py#L214-L232)

## Automated Security Posture

The repository employs an extensive set of automated tools within the CI pipeline to maintain its security posture.

### Security Toolchain
Automated monitoring covers secret auditing, dependency scanning, and static analysis.

*  **Secret Auditing**: Gitleaks, TruffleHog, and detect-secrets scan for leaked credentials.
*  **Dependency Scanning**: `pip-audit`, Safety, OSV-Scanner, Grype, and Trivy check for known vulnerabilities in the `uv.lock` dependency set.
*  **Static Analysis**: Bandit, Semgrep, CodeQL, and dlint analyze Python code for security flaws.
*  **Infrastructure & Workflow**: Checkov audits IaC, while `zizmor` and `actionlint` verify GitHub Actions safety.

Sources: [SECURITY.md:31-38](SECURITY.md#L31-L38)

### Agent Constraints
The project enforces strict workflow boundaries for delegated agents to prevent unauthorized modifications to the repository history.

*  **Branch Protection**: Agents are prohibited from committing directly to the `main` branch.
*  **Worktree Isolation**: Every delegated agent must run in its own isolated worktree.
*  **Token Verification**: WorkOS JWT access tokens are verified with client-specific issuers for backend authentication.

Sources: [AGENTS.md:14-16](AGENTS.md#L14-L16), [tools/skills/Descriptions.py:18](tools/skills/Descriptions.py#L18), [tools/skills/Descriptions.py:38](tools/skills/Descriptions.py#L38)

## Summary
Security Boundaries & Validation in Kit are implemented through a multi-layered approach. It combines runtime path resolution filters, strict data parsing limits (size, ratio, and depth), and an automated suite of security analysis tools. By enforcing these boundaries, the project ensures that CAD conversion processes remain isolated from the host environment and resilient against malformed inputs.
