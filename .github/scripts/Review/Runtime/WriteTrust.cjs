const { mkdirSync, writeFileSync } = require("node:fs");
const { dirname } = require("node:path");
const { rootCertificates } = require("node:tls");

if (!rootCertificates.length)
  throw new Error("The pinned runtime has no certificate authorities");
mkdirSync(dirname(process.argv[2]), { recursive: true });
writeFileSync(process.argv[2], rootCertificates.join("\n") + "\n", {
  mode: 0o644,
});
