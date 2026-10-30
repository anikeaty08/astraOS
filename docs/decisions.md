# Technology decisions and research

Research checked 2026-10-30. Primary sources are linked below. These decisions are specific to AstraOS's current code and goal; “candidate” means implementation has not been selected or verified.

## Decision method

Favor user-visible progress, small integration surface, verifiable behavior, and an upgrade path. For any imported component, check license, maintenance, footprint, toolchain compatibility, and its behavior under AstraOS's threading and memory model before adoption.

| Opportunity | User value now | Dependencies and risk | Decision |
| --- | --- | --- | --- |
| Persistent userspace text workflow | Very high: creates the first reusable personal data | Existing syscalls/VFS/FAT16 can be exercised; needs reboot proof and honest durability limits | **Implement first** |
| TCP/IP networking | High later: communication and package retrieval | Needs frame queues, timers, synchronization, socket ABI, error handling; current driver is raw Ethernet | After file workflow and userspace session |
| Graphical desktop | High later: approachable daily use | Needs app surfaces, input focus, IPC, compositor recovery, fonts; current framebuffer GUI is kernel-owned | After user runtime, input/session model |
| Rewrite bootloader or kernel architecture | Low immediate user value | Large regression surface, no missing user workflow solved | Do not prioritize |

## Concrete choices

### Boot and hardware

Keep Limine as the bootloader and target x86_64 UEFI first. Its [official protocol](https://github.com/limine-bootloader/limine-protocol/blob/trunk/PROTOCOL.md) defines the kernel handoff and memory/framebuffer requests; the [UEFI Forum specification](https://uefi.org/specifications) defines the firmware environment. **Inference:** changing bootloaders now would consume effort without improving the missing file and app workflow. BIOS remains a development path, not the release target.

### Native application interface

Use a small, documented native ABI with bounded pointers and explicit errors. The [Linux VFS documentation](https://docs.kernel.org/filesystems/vfs.html) illustrates why file descriptors, file objects, and filesystem operations are distinct layers. AstraOS can use the principle without copying Linux internals. [newlib's porting documentation](https://sourceware.org/newlib/libc.html) shows that a C library needs a stable set of low-level services. **Inference:** port it after syscall behavior and process startup are stable; current native apps can keep the tiny freestanding runtime.

### Persistent storage

FAT16 currently enables a bootable, host-inspectable disk image and existing write APIs. It is a transitional filesystem for the first normal-reboot gate, not a promise of crash safety. [Linux ext4's journal documentation](https://docs.kernel.org/filesystems/ext4/journal.html) shows the metadata/replay complexity of a mature journaled filesystem. [littlefs's design](https://github.com/littlefs-project/littlefs/blob/master/DESIGN.md) targets recovery from power loss on embedded flash; its guarantees and block assumptions need evaluation before considering it for a PC data volume. **Inference:** do not select either ext4 write support or littlefs by popularity. First measure AstraOS block flush behavior, write ordering, target media, directory/permission needs, and corrupted-image recovery. Keep a decision gate for the data filesystem after those tests. A read-only system image plus separate data volume is a promising later layout, contingent on installer/update design.

### Networking

Evaluate [lwIP](https://www.nongnu.org/lwip/) as the first TCP/IP stack candidate. Its [API documentation](https://www.nongnu.org/lwip/2_1_x/group__api.html) distinguishes callback, sequential, and socket APIs. **Inference:** hide a selected stack behind an AstraOS socket contract; do not expose implementation-specific callbacks to apps. First prove NIC receive/transmit, queues, timers, DHCP/ARP, UDP/TCP, then an app-level exchange and disconnect recovery.

### Graphics

Use a small native userspace compositor with separate app surfaces and input focus. [Wayland's project description](https://wayland.freedesktop.org/index.html) motivates a compositor/client split and protocol-driven IPC, but Wayland compatibility is not a first milestone. **Inference:** this separation allows app crashes without destroying the desktop and prevents apps from drawing over each other. Decide protocol and rendering format after userspace IPC and input delivery work.

## Open decision gates

- **Native data filesystem:** select only after crash-injection, flush support, repair strategy, volume size, and host interoperability needs are recorded.
- **C library:** port newlib or write a small project libc only after a versioned syscall/CRT contract and conformance tests exist.
- **Scheduler/SMP:** add APIC and multicore after single-core locking, interrupt, and process invariants are measured and tested.
- **App/package model:** choose trusted repository format and signatures after persistent storage, networking, and privilege boundaries exist. Do not label the current `/PKG` binary a package manager release.
- **Installer and updates:** choose image/partition layout together with recovery and rollback requirements.

## Research limits

These sources describe upstream technologies, not AstraOS compatibility. No cited source proves current FAT16 writes durable, hardware boot successful, or lwIP/Wayland ported. Those are engineering hypotheses requiring local tests.
