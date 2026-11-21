from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class RequestCancelled(Exception):
    def __init__(self, identity):
        self.identity = identity
        super().__init__(f"research client cancelled request {identity}")


class Connection:
    def __init__(self, launcher, state, startup_ms, revision):
        self.state = state
        self.sequence = 0
        self.messages = queue.Queue()
        self.write_lock = threading.Lock()
        self.pending_lock = threading.Lock()
        self.pending = None
        self.environment = os.environ.copy()
        self.environment["REA_HOPPER_STARTUP_TIMEOUT_MS"] = str(startup_ms)
        self.stderr = (state / "ServerStderr.log").open("w", encoding="utf-8")
        self.process = subprocess.Popen([str(launcher), "--mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, text=True, encoding="utf-8", bufsize=1, env=self.environment)
        self.reader = threading.Thread(target=self.read_messages, daemon=True)
        self.reader.start()
        write_json(state / "Session.json", {"started_at_utc": datetime.now(timezone.utc).isoformat(), "launcher": str(launcher), "server_pid": self.process.pid, "startup_timeout_ms": startup_ms, "source_revision": revision, "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "configuration_files_changed": False})

    def read_messages(self):
        try:
            with (self.state / "ServerMessages.jsonl").open("w", encoding="utf-8") as log:
                for line in self.process.stdout:
                    log.write(line)
                    log.flush()
                    self.messages.put(json.loads(line))
        except BaseException as error:
            self.messages.put(error)
        finally:
            self.messages.put(None)

    def send(self, value):
        with self.write_lock:
            self.process.stdin.write(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")
            self.process.stdin.flush()

    def cancel_current(self, reason):
        with self.pending_lock:
            identity = self.pending
            if identity is None:
                return
            self.send({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": identity, "reason": reason}})
            write_json(self.state / (f"Cancellation{identity:05d}.json"), {"request_id": identity, "reason": reason, "source": "local research client", "native_result_received": False, "cancelled_at_utc": datetime.now(timezone.utc).isoformat()})
            self.messages.put(RequestCancelled(identity))

    def request(self, method, parameters, timeout):
        self.sequence += 1
        identity = self.sequence
        started = time.monotonic()
        with self.pending_lock:
            self.send({"jsonrpc": "2.0", "id": identity, "method": method, "params": parameters})
            self.pending = identity
        write_json(self.state / "Progress.json", {"request_id": identity, "method": method, "parameters": parameters, "started_at_utc": datetime.now(timezone.utc).isoformat(), "completed": False})
        try:
            while True:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise queue.Empty
                response = self.messages.get(timeout=remaining)
                if response is None:
                    raise EOFError("REA server closed its output")
                if isinstance(response, RequestCancelled):
                    if response.identity == identity:
                        raise response
                    continue
                if isinstance(response, BaseException):
                    raise response
                if response.get("id") == identity and "method" not in response:
                    path = self.state / (f"Reply{identity:05d}.json")
                    write_json(path, response)
                    summary = {"request_id": identity, "method": method, "completed": True, "elapsed_seconds": time.monotonic() - started, "reply": str(path), "reply_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "rpc_error": response.get("error"), "tool_error": response.get("result", {}).get("isError", False)}
                    write_json(self.state / "Progress.json", summary)
                    print(json.dumps(summary), flush=True)
                    if "error" in response:
                        raise RuntimeError("REA returned a JSON-RPC error; inspect the retained reply")
                    return response["result"]
                write_json(self.state / "LastServerEvent.json", response)
                if "method" in response and "id" in response:
                    reply = {"jsonrpc": "2.0", "id": response["id"]}
                    if response["method"] == "ping":
                        reply["result"] = {}
                    else:
                        reply["error"] = {"code": -32601, "message": "This research client does not provide optional server-requested capabilities"}
                    self.send(reply)
        except queue.Empty as error:
            self.send({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": identity, "reason": "research request absolute deadline exceeded"}})
            raise TimeoutError(f"REA request {identity} exceeded {timeout} seconds") from error
        finally:
            with self.pending_lock:
                if self.pending == identity:
                    self.pending = None

    def call(self, name, arguments, timeout):
        return self.request("tools/call", {"name": name, "arguments": arguments}, timeout)

    def shutdown(self):
        self.process.stdin.close()
        for action, seconds in ((None, 10), (self.process.terminate, 5), (self.process.kill, 5)):
            if self.process.poll() is not None:
                break
            if action is not None:
                action()
            try:
                self.process.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                continue
        self.stderr.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--startup-ms", type=int, default=900000)
    args = parser.parse_args()
    if not args.launcher.is_absolute() or not args.launcher.is_file() or not os.access(args.launcher, os.X_OK):
        parser.error("launcher must be an installed executable at an absolute path")
    if not args.state.is_absolute() or args.state.resolve().is_relative_to(Path(__file__).resolve().parents[3]):
        parser.error("state must be an absolute new directory outside the repository")
    if not 120000 <= args.startup_ms <= 1800000:
        parser.error("startup deadline must be between two and thirty minutes")
    args.state.mkdir(mode=0o700, parents=True, exist_ok=False)
    connection = Connection(args.launcher, args.state, args.startup_ms, args.source_revision)
    timeout = args.startup_ms / 1000 + 180
    allowed = {"open_binary", "close_binary", "binary_session", "export_evidence_bundle", "list_documents", "list_procedures", "analyze_function", "procedure_callers", "procedure_callees", "procedure_pseudo_code", "procedure_assembly", "xrefs", "inspect_native_instruction", "read_bytes", "address_to_file_offset"}
    initialized = False
    try:
        initialize = connection.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "kit-native-research", "version": "1.0.0"}}, 30)
        if initialize.get("protocolVersion") != "2025-06-18":
            raise RuntimeError("REA did not negotiate the supported MCP protocol revision")
        connection.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        initialized = True
        inventory = []
        cursor = None
        while True:
            result = connection.request("tools/list", {"cursor": cursor} if cursor else {}, 30)
            inventory.extend(result["tools"])
            cursor = result.get("nextCursor")
            if not cursor:
                break
        names = {item["name"] for item in inventory}
        write_json(args.state / "Tools.json", inventory)
        print(json.dumps({"ready": True, "server": initialize["serverInfo"], "tool_count": len(inventory)}), flush=True)
        commands = queue.Queue()
        stopping = threading.Event()

        def read_commands():
            try:
                for line in sys.stdin:
                    command = json.loads(line)
                    if command.get("cancel") is True:
                        connection.cancel_current(str(command.get("reason", "operator cancellation")))
                    else:
                        if command.get("stop") is True:
                            stopping.set()
                            connection.cancel_current("operator requested session stop")
                            commands.put(command)
                            break
                        commands.put(command)
            except BaseException as error:
                commands.put(error)
            finally:
                commands.put(None)

        threading.Thread(target=read_commands, daemon=True).start()
        while True:
            request = commands.get()
            if request is None or stopping.is_set():
                break
            if isinstance(request, BaseException):
                raise request
            if request.get("stop") is True:
                break
            name = request["name"]
            arguments = request.get("arguments", {})
            if name not in allowed or name not in names or not isinstance(arguments, dict):
                raise ValueError("request must name an advertised permitted native analysis tool")
            request_timeout = request.get("timeout_seconds", timeout)
            if type(request_timeout) not in (int, float) or not math.isfinite(request_timeout) or not 0 < request_timeout <= timeout:
                raise ValueError("request deadline must be finite positive seconds within the session limit")
            try:
                connection.call(name, arguments, request_timeout)
            except (RequestCancelled, TimeoutError) as error:
                print(json.dumps({"native_result_received": False, "request_error": str(error)}), flush=True)
    finally:
        try:
            if initialized:
                connection.call("export_evidence_bundle", {"path": str(args.state / "FinalEvidence.json")}, 45)
                cleanup = connection.call("close_binary", {}, 45)
                write_json(args.state / "Cleanup.json", cleanup)
        except BaseException as error:
            write_json(args.state / "CleanupFailure.json", {"error": repr(error), "cleanup_confirmed": False})
        finally:
            connection.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
