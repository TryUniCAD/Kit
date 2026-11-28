import { lookup as Lookup } from "node:dns/promises";
import { writeSync as WriteSync } from "node:fs";
import { request as Request } from "node:https";
import { connect as Connect } from "node:tls";

const KTargets = [
  ["chatgpt.com", "/backend-api/codex/models"],
  ["auth.openai.com", "/oauth/token"],
];
const KBudgetMillis = 8000;
const KPublicCodes = new Set([
  "EAI_AGAIN",
  "ENOTFOUND",
  "ECONNREFUSED",
  "ECONNRESET",
  "ETIMEDOUT",
  "EHOSTUNREACH",
  "ENETUNREACH",
  "ERR_TLS_CERT_ALTNAME_INVALID",
  "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
  "UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
  "SELF_SIGNED_CERT_IN_CHAIN",
  "DEPTH_ZERO_SELF_SIGNED_CERT",
  "CERT_HAS_EXPIRED",
  "PROBE_TIMEOUT",
]);

function MakeTimeout() {
  return Object.assign(new Error("timeout"), { code: "PROBE_TIMEOUT" });
}

async function ResolveHost(Hostname) {
  let Timer;
  try {
    await Promise.race([
      Lookup(Hostname, { all: true }),
      new Promise((Resolve, Reject) => {
        Timer = setTimeout(() => Reject(MakeTimeout()), KBudgetMillis);
      }),
    ]);
  } finally {
    clearTimeout(Timer);
  }
}

function ProbeTls(Hostname) {
  return new Promise((Resolve, Reject) => {
    const Socket = Connect({ host: Hostname, port: 443, servername: Hostname });
    const Timer = setTimeout(
      () => Socket.destroy(MakeTimeout()),
      KBudgetMillis,
    );
    Socket.once("close", () => clearTimeout(Timer));
    Socket.once("error", Reject);
    Socket.once("secureConnect", () => {
      Socket.destroy();
      Resolve();
    });
  });
}

function ProbeHttp(Hostname, PathValue) {
  return new Promise((Resolve, Reject) => {
    const Message = Request(
      { hostname: Hostname, path: PathValue, method: "HEAD", agent: false },
      (Response) => {
        const StatusCode = Response.statusCode;
        Response.destroy();
        if (Number.isInteger(StatusCode)) Resolve(StatusCode);
        else Reject(new Error("missing status"));
      },
    );
    const Timer = setTimeout(
      () => Message.destroy(MakeTimeout()),
      KBudgetMillis,
    );
    Message.once("close", () => clearTimeout(Timer));
    Message.once("error", Reject);
    Message.end();
  });
}

async function Inspect(Hostname, PathValue) {
  let Phase = "dns";
  try {
    await ResolveHost(Hostname);
    Phase = "tls";
    await ProbeTls(Hostname);
    Phase = "http";
    const Status = await ProbeHttp(Hostname, PathValue);
    return { hostname: Hostname, dns: "ok", tls: "ok", http: Status };
  } catch (ErrorValue) {
    return {
      hostname: Hostname,
      phase: Phase,
      error: KPublicCodes.has(ErrorValue?.code)
        ? ErrorValue.code
        : "request-failed",
    };
  }
}

const KResults = await Promise.all(
  KTargets.map(([Hostname, PathValue]) => Inspect(Hostname, PathValue)),
);
for (const Result of KResults) WriteSync(1, `${JSON.stringify(Result)}\n`);
process.exit(KResults.some((Result) => Result.error) ? 1 : 0);
