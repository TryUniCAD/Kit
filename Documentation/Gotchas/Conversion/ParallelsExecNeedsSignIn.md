# Forcing the Windows VM off leaves `prlctl exec` unusable until someone signs in

## Expectation

`prlctl stop "Windows 11" --kill` followed by `prlctl start "Windows 11"` restores the VM, after which
`prlctl exec "Windows 11" ...` works as before and Creo verification can continue.

## Actual behaviour

The VM restarts and `prlctl list` reports `running`, but every exec session fails:

```text
Unable to open new session in this virtual machine. Make sure your virtual machine has finished booting,
runs the latest version of Parallels Tools, and is not isolated from the host OS.
```

This persists after several minutes of boot time and for both the default session and `--current-user`. The
likely cause is that the forced power-off leaves Windows at its sign-in screen, and Parallels Tools only serves
sessions once a user is logged in. Nothing on the host side can complete that.

The trigger is worth recording: a `modelcheck.bat` run wedged the guest agent (exec sessions returned nothing at
all, while `prlctl list` still said `running`), and the forced restart that followed did not bring exec back
without a sign-in.

## Workaround

Sign in to the Windows VM on the console (Parallels Desktop → the VM window), then `prlctl exec` works again.
Before forcing a restart, check whether the agent is merely slow: `prlctl exec "Windows 11" whoami` returning
nothing at all — not even an error — is the wedged state, and it can be worth one more attempt after a minute.

## Evidence

- `Documentation/Gotchas/Conversion/CreoModelCheckUnattended.md` — the ModelCHECK run that wedged it.
- `prlctl list` output showing the VM as `running` while exec fails.
