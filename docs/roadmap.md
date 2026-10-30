# Feature inventory and delivery plan

Status words mean: **verified** has a passing repository/QEMU check; **present** exists but the end-to-end user contract is not proven; **planned** has no complete implementation. This inventory is intentionally broader than the next implementation slice.

## Verified baseline

- **Boot and console:** Limine-loaded x86_64 kernel, serial output, kernel shell; `make smoke` exercises QEMU boot.
- **User process recovery:** ring 3 ELF, syscalls, faults contained, exit/reap; `make fault-smoke` passes.
- **User timer preemption and background jobs:** two CPU-bound processes run while the kernel shell responds, both can be killed, and process slots are reused; `make preemption-smoke` passes.

## Present but unproven as complete workflows

- FAT16/VFS create, read, write, truncate, unlink and rename primitives. A full-disk write failure now preserves the original file through temporary-file replacement; interruption during rename or power loss is not yet proven.
- A userspace single-line `write` command and `make persistence-smoke` now prove create, replace, and exact readback after a normal QEMU guest reboot. This is narrower than an editor or crash-safe storage.
- A standalone bounded line editor and `make editor-smoke` prove multi-line editing, discard, and reboot readback.
- The userspace shell is the default session after login; `make session-smoke` proves bounded restart and kernel recovery fallback. Login/supervision remain kernel-owned, and signals, job control and terminal ownership are still incomplete.
- `/PKG` is present but not a verified package-management workflow.
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

1. **Userspace session continuation** — add app argument passing, explicit terminal ownership/signals, and later a userspace init/service manager. The default shell and bounded kernel supervisor now pass QEMU checks.
2. **Durability API** — define append and flush semantics at the syscall/VFS/block boundaries, then add interrupted-write tests. This is separate from normal reboot persistence.

## Release gates

- Build from clean checkout with pinned dependencies and documented toolchain.
- Automated boot, fault, preemption, persistent-file, editor, full-disk save-failure, and session checks pass in CI.
- Each advertised driver/workflow has a reproducible test and known limitations.
- Physical-hardware claims identify machine model, firmware, storage, input and display devices.
- No “durable” or “crash-safe” claim until write-cache flush and interrupted-write evidence exists.
