# AstraOS progress

## 2026-10-30: first development slice

- Objective: grow AstraOS into a usable independent OS. The first slice is
  user fault isolation: a bad ring-3 program must not halt the kernel.
- Baseline: initial clean Git worktree at `150cd3e`. The original smoke check
  only looked for a pre-shell boot marker.
- Implemented user fault termination in `isr.c`, foreground waiting in the
  kernel shell, deferred scheduling from its loop, and a real `/FAULT` guest
  program with a serial integration check.
- Runtime investigation exposed and fixed syscall register clobbering,
  unsupported SSE instructions in userspace, incomplete PCI driver
  registration, a boot-order mistake, missing Limine build setup, two
  warning-as-error build failures, and CRLF in the shell smoke script.
- Verification: `make smoke` and `make fault-smoke` both passed after a clean
  build on WSL Ubuntu-24.04. The fault test observed PID 1 fault vector 6 and
  status -7, followed by `/HELLO` output and PID 2 status 0.
- Repository reproducibility: removed generated `.o`, ISO, ISO payloads, and
  an unmapped Limine gitlink from the Git index; local build products and the
  Limine checkout remain available and are ignored. Added line-ending rules
  for shell and Python scripts.
- Remaining risk: normal user processes can still monopolize the CPU because
  scheduling is only reached at cooperative/kernel-shell points. The process
  lifecycle test for repeated children and reuse remains pending.
- Next action: verify repeated process creation and slot reuse, then make
  userspace scheduling robust enough that a busy user program cannot freeze
  the shell.

## 2026-10-30: user preemption and background jobs

- Implemented timer-driven switching for ring-3 code. The timer IRQ acknowledges
  hardware before switching and leaves zombie cleanup for ordinary scheduling.
- Added `run <binary> &` and `kill <pid>` to the kernel shell, process detach
  ownership, and credential checks when killing another process.
- Added `/SPIN` and `make preemption-smoke`. The test launched two busy user
  programs, observed both run, used `uptime` while they were active, killed
  them, and then launched 70 `/HELLO` children successfully.
- Verification after the final PIT flag fix: `make smoke`, `make fault-smoke`,
  and `make preemption-smoke` all passed from a clean WSL Ubuntu build.
- Remaining scope: the primary shell still runs in the kernel. Blocking
  syscalls and device I/O do not yet have a complete user-process scheduling
  model. Persistent files and real hardware remain unverified.
- Next action: research and choose the next user-visible OS workflow, plan it
  against current capabilities, then implement and verify it end to end.
