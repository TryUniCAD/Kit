const Phases = require("../CiPhases.json");
const WorkflowRoot = ".github/workflows/";
const WorkflowPath = WorkflowRoot + "PullRequest.yml";
const QueuePath = WorkflowRoot + "MergeQueue.yml";
const QueueGate = "Merge queue acceptance";
const QueueJobs = [
  "Run the complete test suite",
  "Test suite / Plan",
  "Test suite / Report",
  "Test suite / Platform (windows-2025)",
  "Test suite / Platform (windows-2025) / shard-1",
  "Test suite / Platform (windows-2025) / shard-2",
  "Test suite / Platform (windows-2025) / shard-3",
  "Test suite / Platform (windows-2025) / shard-4",
  "Test suite / Platform (macos-26)",
  "Test suite / Platform (macos-26) / shard-1",
  "Test suite / Platform (macos-26) / shard-2",
  "Test suite / Platform (macos-26) / shard-3",
  "Test suite / Platform (macos-26) / shard-4",
  "Linux kernel OOM witness",
  "Analyze actions",
  "Analyze python",
  "Analyze javascript-typescript",
  "Analyze java-kotlin",
  "Bandit",
  "Semgrep",
  "pip-audit",
  "Safety",
  "Checkov",
  "detect-secrets",
  "Syft",
  "CycloneDX SBOM",
  "dlint",
  "Gitleaks",
  "Grype",
  "OSV-Scanner",
  "Scorecard",
  "Trivy",
  "TruffleHog",
];
const ShardJobs = /^Test suite \/ Shard \(\d+\)$/;
const RetiringJobs = {
  "WorkflowQuality.yml": ["Research CLI compatibility"],
};
const PreflightNames = {
  "PythonQuality.yml": "PR CI reuse (Python quality gate)",
  "PythonSteering.yml": "PR CI reuse (Python steering)",
  "ExplicitImports.yml": "PR CI reuse (Explicit imports)",
  "PathPolicies.yml": "Validation phase (PathPolicies)",
  "SteeringSync.yml": "PR CI reuse (Steering synchronization)",
  "WorkflowPins.yml": "PR CI reuse (Workflow pins)",
  "RationaleComments.yml": "Validation phase (RationaleComments)",
  "WorkflowQuality.yml": "PR CI reuse (Workflow quality)",
};
const TargetChecks = {
  "PullRequestCI.yml": "Label CI changes",
  "PullRequestTests.yml": "Label test changes",
  "PullRequestDependencies.yml": "Label dependency changes",
  "PullRequestDocumentation.yml": "Label documentation changes",
  "PullRequestSize.yml": "Label changed LOC ratio",
  "PullRequestBreakingChange.yml": "Label declared breaking changes",
  "PullRequestDirection.yml": "Label dominant change direction",
  "PullRequestDiffBreakdown.yml": "Publish diff breakdown",
};

function CiWorkflows(IsPull, IncludeAgg = false, Opened = false) {
  const Event = IsPull ? "pull_request" : "merge_group";
  const Required = IsPull ? Phases.PullRequest : Phases.MergeQueue;
  const Deferred = IsPull ? Phases.MergeQueue : Phases.PullRequest;
  const Workflows = new Map(
    Object.entries(PreflightNames).map(([File, Name]) => {
      const OtherPhaseOnly = Deferred[File].filter(
        (Job) => !Required[File].includes(Job),
      );
      const Retiring = RetiringJobs[File] ?? [];
      if (IsPull && File === "WorkflowQuality.yml")
        OtherPhaseOnly.push(
          "Research CLI Windows compatibility / ${{ matrix.group }}",
          "Native file compatibility / ${{ matrix.group }}",
        );
      return [
        WorkflowRoot + File,
        {
          event: Event,
          required: Required[File].filter((Job) => !Retiring.includes(Job)),
          optional: [...OtherPhaseOnly, ...Retiring],
          skip: OtherPhaseOnly,
          preflight: Name,
        },
      ];
    }),
  );
  if (!IsPull) {
    Workflows.set(QueuePath, {
      event: Event,
      required: [QueueGate, ...QueueJobs],
      matching: [ShardJobs],
      optional: [
        "CAD feature decoding session",
        "Test suite / Platform (windows-2025) / shard-5",
        "Test suite / Platform (macos-26) / shard-5",
      ],
      skip: [
        "CAD feature decoding session",
        "Test suite / Platform (windows-2025) / shard-5",
        "Test suite / Platform (macos-26) / shard-5",
      ],
    });
    return Workflows;
  }

  const QueueDeferred = [
    ...QueueJobs,
    "Test suite / Platform (windows-2025) / shard-5",
    "Test suite / Platform (macos-26) / shard-5",
    "CAD feature decoding session",
    "Analyze ${{ matrix.language }}",
    "Test suite / Shard (${{ matrix.shard }})",
    "Test suite / Platform (windows-2025) / ${{ matrix.group }}",
    "Test suite / Platform (macos-26) / ${{ matrix.group }}",
  ];
  Workflows.set(QueuePath, {
    event: Event,
    required: [QueueGate],
    optional: QueueDeferred,
    skip: QueueDeferred,
  });
  Workflows.set(WorkflowRoot + "ReleaseBuild.yml", {
    event: Event,
    required: ["Build and verify release artifacts"],
  });
  for (const [File, Name] of Object.entries(TargetChecks))
    Workflows.set(WorkflowRoot + File, {
      event: "pull_request_target",
      required: [Name],
    });

  const FirstTime = ["Label first-time contributors"];
  Workflows.set(WorkflowRoot + "PullRequestFirstTimeContributor.yml", {
    event: "pull_request_target",
    required: Opened ? FirstTime : [],
    optional: FirstTime,
  });
  if (IncludeAgg)
    Workflows.set(WorkflowPath, {
      event: "pull_request_target",
      required: ["CI Agg"],
    });
  return Workflows;
}

module.exports = { CiWorkflows, WorkflowPath };
