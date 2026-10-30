# AstraOS vision

## Product thesis

AstraOS should become a small, independent, **usable personal operating system** for a documented set of x86_64 UEFI computers. A user should be able to boot it, create and edit files, run isolated applications, connect to a network, and recover from an application failure without needing the developer to intervene. Building those workflows from the kernel upward remains a learning goal, but user-visible behavior decides whether a milestone is complete.

The initial audience is one technical user on a QEMU virtual machine and then on named physical machines. The first useful release is a reliable text workstation: boot, log in, use a userspace shell and editor, save work, reboot, and read the exact saved data. A graphical desktop and network applications follow only after that contract holds. This is an engineering target, not a claim of Linux/Windows application compatibility.

## What “good” means here

| Quality | Observable acceptance |
| --- | --- |
| Useful | A person can create, modify, find, and reopen their own work with user applications. |
| Reliable | Normal reboot preserves data; interrupted writes are tested and reported honestly. |
| Recoverable | A crashing or looping application does not take down the shell or other applications. |
| Understandable | Interfaces, errors, supported hardware, and limitations are documented. |
| Installable | A reproducible image and a tested installation or live-boot path exist. |
| Extensible | Applications use a stable, versioned ABI rather than kernel internals. |

## Product shape

The differentiator should be **recovery and visibility built into the experience**. Later releases should show what failed, which file or process was affected, and what the OS did to recover. A safe mode, process crash reports, storage health checks, and eventually snapshots should be ordinary OS features. These are proposed features, not implemented ones. The value comes from an OS a user can trust and diagnose, not from an unusual kernel mechanism by itself.

## Scope and constraints

- Target x86_64 with UEFI first; BIOS/QEMU may remain a development path. Extend architectures only after the first supported machine is proven.
- One local user and a small set of bundled native ELF programs first. Later credentials and multi-user isolation need a new security review.
- C and assembly for the current kernel and runtime. Other languages can be evaluated when the ABI, toolchain, and memory model are mature.
- QEMU is the integration test platform. Hardware support is declared per tested device and machine, never inferred from QEMU success.
- Avoid claiming POSIX, Wayland, or Linux binary compatibility without conformance tests. A familiar API shape is useful, but compatibility is a separate deliverable.

## Current baseline (2026-10-30)

The repository boots a Limine-loaded x86_64 kernel. It has virtual memory, ring 3 ELF loading, system calls, a kernel recovery shell, a default userspace shell, FAT16/VFS read and write primitives, and several device drivers. Automated QEMU checks demonstrate user fault containment, preemption of two CPU-bound user processes, process-slot reuse, text saves across normal reboot, and fallback from a failed userspace session. This does **not** prove storage survives power loss, networking works at the application layer, physical hardware is supported, or the desktop is usable.

The first user-visible proof is now a single-line userspace save and replacement that survives a normal QEMU guest reboot. A complete multi-line editor, interrupted-write recovery, and physical hardware remain open work. See [the focused feature contract](features/persistent-text.md).
