# AstraOS

AstraOS is an experimental x86_64 operating system written primarily in C. The goal is a small, independent **usable personal OS**: boot, run isolated applications, create and keep files, connect to a network, and eventually use a restartable desktop on documented UEFI machines.

The [vision](docs/vision.md), [system architecture](docs/architecture.md), [researched technology decisions](docs/decisions.md), and [feature roadmap](docs/roadmap.md) describe the full direction in focused documents. The [design index](docs/README.md) links the parts. The first active slice is the [persistent text workflow](docs/features/persistent-text.md).

## What works today

- Limine boot into an x86_64 kernel with serial/framebuffer console and a kernel recovery shell.
- Physical and virtual memory management, ring 3 ELF programs, syscalls, process scheduling and fault isolation.
- Timer preemption of user programs, background launch/kill, exit/reap, and a basic userspace shell.
- VFS and FAT16 file-operation primitives; storage persistence and power-loss safety are **not yet verified** as user workflows.
- Device-driver code including ATA, AHCI, NVMe, USB and RTL8139. Presence of a driver does not imply tested hardware support or a working TCP/IP stack.

QEMU integration checks currently cover boot, user fault recovery, preemption, and process-slot reuse. The default interactive shell is still kernel-owned. No supported physical-machine release, userspace desktop, or application-level networking is claimed yet.

## Build and run

On Linux or WSL, install GCC, binutils, NASM, xorriso, dosfstools, mtools, Python 3, QEMU, and Git. The Makefile fetches a Limine `v8.x-binary` checkout into `limine/` when needed.

```sh
make iso
make disk
make run
```

`make disk` creates a new 32 MiB FAT16 image with sample programs. **It replaces `disk.img`**, so keep a copy or skip that target when preserving data. `make run` depends on `disk` and therefore also recreates the disk image; use the direct QEMU invocation below to reopen an existing image:

```sh
qemu-system-x86_64 -cdrom astraos.iso -boot order=d \
  -drive file=disk.img,format=raw,if=ide -m 256M -serial stdio
```

At the kernel shell, try `help`, `ls /`, `run /HELLO`, or `run /SH` to enter the userspace shell. User-program and shell capabilities are evolving; see the focused feature document for the current save workflow.

## Checks

```sh
make smoke
make fault-smoke
make preemption-smoke
```

These checks use QEMU. They do not establish crash-safe file writes or real-hardware support. The [feature tracker](.agent-state/feature-list.json) records acceptance evidence.

## Repository layout

| Path | Purpose |
| --- | --- |
| `kernel/arch/x86_64/`, `kernel/mm/`, `kernel/proc/` | CPU boundary, memory, and processes |
| `kernel/fs/`, `kernel/drivers/`, `kernel/shell/` | Storage, hardware, and recovery shell |
| `userspace/` | Native ELF programs and syscall wrapper |
| `scripts/` | QEMU integration checks |
| `docs/` | Vision, architecture, decisions, roadmap and feature contracts |
| `.agent-state/` | Current product contract, progress, and machine-readable feature evidence |

## License

MIT. Check the repository license terms before redistribution.
