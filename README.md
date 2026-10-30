# AstraOS

AstraOS is an experimental x86_64 operating system written primarily in C. The goal is a small, independent **usable personal OS**: boot, run isolated applications, create and keep files, connect to a network, and eventually use a restartable desktop on documented UEFI machines.

The [vision](docs/vision.md), [system architecture](docs/architecture.md), [researched technology decisions](docs/decisions.md), and [feature roadmap](docs/roadmap.md) describe the full direction in focused documents. The [design index](docs/README.md) links the parts, including the [repository layout](docs/repository-layout.md). The first active slice is the [persistent text workflow](docs/features/persistent-text.md).

## What works today

- Limine boot into an x86_64 kernel with serial/framebuffer console and a kernel recovery shell.
- Physical and virtual memory management, ring 3 ELF programs, syscalls, process scheduling and fault isolation.
- Timer preemption of user programs, background launch/kill, exit/reap, and a default userspace shell with foreground child execution. The kernel shell is available when the user shell exits or fails to start.
- A standalone bounded line editor (`/EDIT`) with print, append, insert, delete, save, and discard commands.
- VFS and FAT16 file operations. Userspace replacement writes a temporary file first and preserves the old file on a tested full-disk write failure. Normal QEMU reboot persistence passes; power-loss safety is **not verified**.
- Device-driver code including ATA, AHCI, NVMe, USB and RTL8139. Presence of a driver does not imply tested hardware support or a working TCP/IP stack.

QEMU integration checks currently cover boot, user fault recovery, preemption, process-slot reuse, the default userspace session, and text workflows. Login and the limited session supervisor are still kernel-owned. No supported physical-machine release, userspace desktop, or application-level networking is claimed yet.

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

After login, AstraOS starts the userspace shell at `user$ `. Try `run /HELLO` or `run /EDIT`; the editor asks for a root-level 8.3 path such as `/NOTE.TXT`. Type `h` for editor commands and `w` to save. `exit` returns to the kernel recovery shell at `$ `, and `exit 1` exercises supervised restart. The editor currently supports up to 32 lines of 95 bytes each. See the [editor feature contract](docs/features/text-editor.md) and [session contract](docs/features/userspace-session.md) for limits.

## Checks

```sh
make smoke
make fault-smoke
make preemption-smoke
make persistence-smoke
make editor-smoke
make save-failure-smoke
make session-smoke
```

These checks use QEMU. The persistence and editor checks recreate `disk.img` once, then reboot without recreating it and check exact bytes. The full-disk check verifies that an ordinary failed replacement leaves the original intact. The checks do not establish crash-safe file writes or real-hardware support. The [feature tracker](.agent-state/feature-list.json) records acceptance evidence.

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
