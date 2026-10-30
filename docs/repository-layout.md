# Repository structure and migration

The code is being separated by ownership as features are built. Moving every file at once would make failures harder to locate and tests harder to trust, so each move happens with the feature it serves.

## Current ownership map

```text
kernel/
  arch/x86_64/   CPU entry, interrupts, syscall boundary
  mm/            Physical/virtual memory and heap
  proc/          Processes, scheduler, descriptors
  fs/            VFS and FAT16 implementation
  drivers/       Hardware access
  gui/           Current kernel display UI
  shell/         Recovery shell and login
userspace/
  sh.c           Userspace shell loop and command dispatch
  shell/         Shell command modules
  runtime/       Shared user file replacement; later CRT/libc helpers
  syscall.h      Current native syscall wrapper
  *.c            Other independent ELF programs
scripts/         QEMU integration checks
docs/            Product and system design, split by concern
.agent-state/    Progress and machine-readable acceptance evidence
```

## Target shape, introduced incrementally

```text
kernel/
  arch/          Architecture-specific entry and interrupt code
  core/          Common scheduler, process, IPC and syscall services
  mm/            Memory ownership and mappings
  fs/            VFS, filesystem drivers and block interface
  drivers/       Device-specific drivers
  diagnostics/   Structured faults and trace/event records
userspace/
  runtime/       CRT, syscall wrappers and later libc port
  init/          Service/session supervision
  shell/         Shell parser and command modules
  apps/          Editor, file tools, diagnostics, network clients
  desktop/       Compositor and UI applications
scripts/         Build/image and integration-test tooling
docs/            Architecture, decision records and feature contracts
```

The target is a module ownership guide, not an instruction to create empty directories. New code goes in the relevant home when its interface is designed. Existing kernel files move only when tests can verify the refactor. `userspace/shell/file_commands.c` handles shell file commands, `userspace/runtime/file_replace.c` handles shared replacement, and `userspace/sh.c` remains the shell entry and dispatch.

## Module rules

- Architecture code may call common kernel services; common services should not depend on x86_64 headers except behind narrow interfaces.
- Filesystems call a block-device interface, not individual disk drivers. Applications call the syscall ABI, not kernel headers or on-disk routines.
- Drivers report events and I/O results; session, filesystem, and desktop policy lives above them.
- Cross-module contracts belong in headers and docs with error and ownership rules. Avoid folders named after vague phases or teams.
