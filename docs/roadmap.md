# Feature inventory and delivery plan

Status words mean: **verified** has a passing repository/QEMU check; **present** exists but the end-to-end user contract is not proven; **planned** has no complete implementation. This inventory is intentionally broader than the next implementation slice.

## Verified baseline

- **Boot and console:** Limine-loaded x86_64 kernel, serial output, kernel shell; `make smoke` exercises QEMU boot.
- **User process recovery:** ring 3 ELF, syscalls, faults contained, exit/reap; `make fault-smoke` passes.
- **User timer preemption and background jobs:** two CPU-bound processes run while the kernel shell responds, both can be killed, and process slots are reused; `make preemption-smoke` passes.

## Present but unproven as complete workflows

- FAT16/VFS create, read, write, truncate, unlink and rename primitives; no user-edit/reboot acceptance test yet.
- Basic userspace shell and `/PKG`; userspace shell is not the default session and has no text editing command.
- Framebuffer GUI, input, PCI, disk, USB and raw NIC drivers; named physical-machine support and a full userspace desktop/network service are not proven.

## Milestones in dependency order

| Milestone | Small implementation slices | User-visible acceptance |
| --- | --- | --- |
| 1. Persistent text workstation | Userspace file editing → exact readback → same disk after reboot → invalid/short-write handling → later crash-injection/flush | Create and change a note, reboot, reopen the exact bytes. A failed save reports an error. |
| 2. Userspace session | Init supervision → default userspace shell → console ownership and signals → app arguments/environment → editor as independent ELF app | Boot to a restartable userspace shell; launch/stop apps and return after a crash. |
| 3. Robust data volume | Block flush contract → fault injection → filesystem decision → fsck/recovery/backup → install layout | An interrupted save is either recoverable or explicitly diagnosed; unrelated files survive. |
| 4. Network workstation | NIC queues → stack integration → IP/DHCP/DNS → UDP/TCP/socket ABI → one useful client → link-loss tests | Configure network and exchange app data with a host, including disconnect recovery. |
| 5. Native desktop | Input events/focus → surface/IPC ABI → compositor → text rendering/windows → file manager/editor → crash restart | Switch between two apps; one can fault without freezing input or the other. |
| 6. Installable release | UEFI install/live medium → supported hardware matrix → updates/rollback → diagnostics/safe mode → documentation | Install/boot on a named x86_64 machine; perform the core text workflow there. |

## Full capability backlog

**Platform:** UEFI boot, ACPI power control, APIC/IOAPIC, SMP, timer source migration, suspend/resume, real-machine compatibility matrix. **Memory/process:** page ownership, guard pages, demand paging, resource limits, safe user copying, process signals, user IPC, shared memory. **Storage:** per-process descriptors, access modes, directories, timestamps, mount points, device filesystem, flush/fsync, recovery, data filesystem, backup/snapshots. **User environment:** init, login/session policy, shell, arguments/environment, terminal, editor, file tools, C library, documentation, app packaging. **Network:** drivers, ARP, IPv4, DHCP, DNS, UDP, TCP, socket ABI, TLS strategy, network tools. **Graphics/input:** input routing, fonts, surfaces, compositor, window management, accessible keyboard controls, file manager. **Trust/release:** permission model, executable integrity, secure update path, crash reporting, installer, reproducible builds, CI/QEMU, hardware tests.

This backlog is a direction, not a promise that all items belong in one release. The sequence is driven by acceptance gates and dependencies, not by novelty.

## Next two engineering slices

1. **Userspace text command and reboot test** — scope in [persistent-text.md](features/persistent-text.md). Touch userspace shell, a dedicated QEMU test, and docs. Avoid kernel changes unless a failing contract requires one.
2. **Durability API** — after slice 1's writable-open mode, define append and flush semantics at the syscall/VFS/block boundaries, then add interrupted-write tests. This is separate from simply demonstrating normal reboot persistence.

## Release gates

- Build from clean checkout with pinned dependencies and documented toolchain.
- Automated boot, fault, preemption, and persistent-file checks pass in CI.
- Each advertised driver/workflow has a reproducible test and known limitations.
- Physical-hardware claims identify machine model, firmware, storage, input and display devices.
- No “durable” or “crash-safe” claim until write-cache flush and interrupted-write evidence exists.
