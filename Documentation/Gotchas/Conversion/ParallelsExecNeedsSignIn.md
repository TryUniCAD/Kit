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

## The VM can also wedge in `stopping`, and `prlctl` cannot clear it

After the agent wedged, `prlctl stop`, `prlctl stop --kill` and `prlctl reset` all refused with:

```text
Failed to stop the VM: Unable to complete the operation. This operation cannot be completed because
"Windows 11" is in the "stopping" state.
```

and `prlctl list --all` kept reporting `stopping` indefinitely — the hypervisor process itself was stuck. Clearing it
needed the host side:

```text
ps -Ao pid,etime,command | grep prl_vm_app      # the stuck process, 43 minutes old
kill -9 <pid>                                    # VM then reports `stopped`
prlctl start "Windows 11"
```

That restores the VM to `running`, but **not** to a working exec session: `prlctl list` still shows no IP address and
both the default and `--current-user` sessions fail with `Unable to open new session`, which is consistent with
Windows sitting at its sign-in screen with Parallels Tools not yet serving.

## The VM can also enter a boot loop that `prlctl capture` exposes

After the forced power-off the guest did not settle at a sign-in screen. `prlctl capture` is the only way to see it
from a headless host (there is no GUI session, so `screencapture` fails with `could not create image from display`):

```text
prlctl capture "Windows 11" --file /tmp/vm.png
```

Two captures two minutes apart both showed the Windows logo with a spinning dot — the dot had moved, so the guest was
progressing, not frozen. Minutes later the VM cycled `stopping` → `running` on its own, and capture then failed:

```text
PrlDevDisplay_ConnectToVm: PrlJob_Wait: PRL_ERR_IO_STOPPED
```

That is a boot loop rather than a login screen, so no amount of waiting yields an exec session. `prlctl stop --kill`
still worked at that point and returned the VM to `stopped`.

## Workaround

Sign in to the Windows VM on the console (Parallels Desktop → the VM window), then `prlctl exec` works again.
Before forcing a restart, check whether the agent is merely slow: `prlctl exec "Windows 11" whoami` returning
nothing at all — not even an error — is the wedged state, and it can be worth one more attempt after a minute.

## Evidence

- `Documentation/Gotchas/Conversion/CreoModelCheckUnattended.md` — the ModelCHECK run that wedged it.
- `prlctl list` output showing the VM as `running` while exec fails.
