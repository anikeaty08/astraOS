# AstraOS build and verification runbook

## Build environment

The Makefile uses POSIX shell tools. On Linux or WSL Ubuntu, the README lists
GCC, NASM, xorriso, dosfstools, mtools, QEMU, and Git as prerequisites. Limine
is cloned by `make iso` if absent.

```sh
make iso
make disk
make run
```

Checks:

```sh
make smoke
make fault-smoke
make preemption-smoke
```

`make smoke` cleans and rebuilds the image, then waits for
`ASTRAOS_SMOKE_READY` on serial output. `make fault-smoke` boots with a serial
console, logs in, runs `/FAULT`, verifies an isolated user fault and nonzero
exit, then runs `/HELLO` and verifies output and zero exit.
`make preemption-smoke` runs two CPU-bound `/SPIN` jobs, verifies the shell
remains responsive, kills both jobs, and launches 70 further programs to
verify process slot reuse.

## Current local environment (2026-10-30)

Windows workspace: `C:\Users\anike\Desktop\os-kernel`.
WSL Ubuntu-24.04 now has `make`, `gcc`, `nasm`, `qemu-system-x86_64`,
`xorriso`, `mkfs.fat`, and `mcopy`. The initial probe lacked the latter five;
they were installed for this development slice. Recheck after environment
changes. Both `make smoke` and `make fault-smoke` passed after a clean build.

This worktree originally tracked `.o` files and boot images. This development
slice removes them from the index and ignores future generated copies. Run
`make clean` once in an existing checkout before relying on an incremental
build, because old local files may remain after the index cleanup.

## Verification discipline

Run a clean kernel and userspace build, then the boot smoke check. For each
feature, run its acceptance steps through the shell or userspace ABI and record
the exact command and result in `feature-list.json` and `progress.md`.
