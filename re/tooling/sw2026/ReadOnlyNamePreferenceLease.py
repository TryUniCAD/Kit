from ComponentNamePreferenceLease import PreferenceLease, durable, require


class ReadOnlyNamePreferenceLease(PreferenceLease):
    def row(self, stage):
        return {
            **super().row(stage),
            "schema": "kit.sw2026.component-name-readonly-preference-lease.v1",
            "authorized_scope": "one owned read-only native name observation only",
            "original_true_required": True,
            "document_setter_calls": 0,
            "file_saves": 0,
        }

    def begin(self):
        self.original = bool(
            self.author.get(self.author.app, "GetUserPreferenceToggle", 18)
        )
        durable(
            self.directory / "Captured.json",
            self.row("original-captured-before-any-mutation"),
        )
        require(
            self.original is True,
            "read-only name discriminator requires the actual original true setting",
        )
        armed = self.row("restoration-armed-before-any-mutation")
        armed["recovery_required_if_no_restored_receipt"] = True
        durable(self.directory / "Armed.json", armed)
        self.setter_calls += 1
        returned = self.author.get(
            self.author.app, "SetUserPreferenceToggle", 18, False
        )
        current = bool(self.author.get(self.author.app, "GetUserPreferenceToggle", 18))
        applied = self.row("temporary-readback-before-read-only-open")
        applied.update(
            setter_return=returned, actual_value=current, applied=current is False
        )
        durable(self.directory / "Applied.json", applied)
        require(current is False, "read-only observation setting did not apply")
        return self.original
