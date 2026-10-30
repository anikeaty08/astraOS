# Feature contract: default userspace session

## User-visible behavior

After login, AstraOS starts `/SH` as the normal foreground shell. The kernel shell remains the recovery interface: `exit` in `/SH` returns to it. A nonzero exit restarts `/SH` up to three consecutive times, then returns to recovery with a clear reason. If `/SH` is missing or cannot start, login still reaches the recovery shell.

This is a **transitional kernel-owned supervisor**. The initial implementation and QEMU acceptance check are complete. It makes the normal interactive program a userspace process now, while a future userspace init/service manager can own session policy once IPC, signals, and a terminal API exist. The kernel owns initial login and emergency fallback.

## Boundaries

- The shell subsystem owns login, normal-session policy, and the recovery prompt. It reuses one foreground process-launch helper rather than copying ELF loading logic.
- The process subsystem owns child creation, parent relationship, exit status, and resource cleanup. The session helper passes the authenticated UID/admin state into the launched process.
- The process subsystem tracks the foreground console reader. A foreground child receives input and returns it on exit or kill; a background app's console read fails. The kernel waits for `/SH`, and `/SH` waits for a foreground app such as `/EDIT`. This is not a full terminal implementation.
- A clean shell exit is a deliberate request for recovery mode. A failed launch or three nonzero exits also enters recovery. The recovery shell can run `/SH` manually.

## Acceptance

1. Login reaches `user$ ` without a manual `run /SH` command.
2. `run /EDIT` from the default shell opens the editor; on exit input returns to `user$ `.
3. `exit` returns to the kernel `$ ` prompt; kernel recovery commands still work.
4. An explicit `exit 1` causes a supervised restart and a new `user$ ` prompt. Repeated failures stop at the recovery prompt.
5. A temporary copy of the disk missing `/SH` falls back to recovery without hanging; the primary test image keeps its shell.
6. Existing boot, fault, preemption, persistence, editor, and save-failure tests pass after adapting their prompt expectations.
7. Foreground `/INPUT` reads a line, while background `/INPUT` is denied and the recovery shell remains responsive.

## Limits and next work

The kernel still performs login and owns this supervisor. A bounded argument vector now reaches native apps, but environment variables, signals, PTYs, job-control groups, a service dependency graph, and automatic relaunch after an unkillable kernel fault are absent. `process_wait` currently yields in a loop. Those are explicit later session/runtime tasks; none are implied by the word “session” here.
