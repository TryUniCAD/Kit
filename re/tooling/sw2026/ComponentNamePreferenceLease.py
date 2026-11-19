import json
import os
from pathlib import Path
import time


def require(value, message):
    if not value:
        raise ValueError(message)


def durable(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())


class PreferenceLease:
    def __init__(self, author, directory, packet_sha256, identity):
        self.author = author
        self.directory = Path(directory)
        self.packet_sha256 = packet_sha256
        self.identity = identity
        self.original = None
        self.restored = False
        self.setter_calls = 0

    def row(self, stage):
        return {
            "schema": "kit.sw2026.component-name-preference-lease.v1",
            "packet_sha256": self.packet_sha256,
            "stage": stage,
            "recorded_at_ns": time.time_ns(),
            "preference_enum": 18,
            "original_value": self.original,
            "temporary_value": False,
            "oracle_identity": self.identity,
            "setter_calls": self.setter_calls,
            "authorized_scope": "one owned source author/save session only",
        }

    def begin(self):
        self.original = bool(
            self.author.get(self.author.app, "GetUserPreferenceToggle", 18)
        )
        durable(
            self.directory / "Captured.json",
            self.row("original-captured-before-any-mutation"),
        )
        armed = self.row("restoration-armed-before-any-mutation")
        armed["recovery_required_if_no_restored_receipt"] = True
        durable(self.directory / "Armed.json", armed)
        result = None
        if self.original is not False:
            self.setter_calls += 1
            result = self.author.get(
                self.author.app, "SetUserPreferenceToggle", 18, False
            )
        current = bool(self.author.get(self.author.app, "GetUserPreferenceToggle", 18))
        applied = self.row("temporary-readback")
        applied.update(
            setter_return=result, actual_value=current, applied=current is False
        )
        durable(self.directory / "Applied.json", applied)
        require(
            current is False,
            "the owned temporary component-name preference did not apply",
        )
        return self.original

    def restore(self):
        if self.original is None:
            return None
        before = bool(self.author.get(self.author.app, "GetUserPreferenceToggle", 18))
        result = None
        if before != self.original:
            self.setter_calls += 1
            result = self.author.get(
                self.author.app, "SetUserPreferenceToggle", 18, self.original
            )
        after = bool(self.author.get(self.author.app, "GetUserPreferenceToggle", 18))
        self.restored = after == self.original
        row = self.row("original-restoration-readback")
        row.update(
            actual_before_restore=before,
            actual_after_restore=after,
            setter_return=result,
            restored=self.restored,
        )
        durable(self.directory / "Restored.json", row)
        require(self.restored, "the original application preference was not restored")
        return row
