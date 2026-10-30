# AstraOS product direction

## Purpose

Grow AstraOS from a bootable hobby kernel into a usable, independently built
x86_64 operating system. The primary user is a technically curious person who
can boot supported hardware, run applications, and keep their work across
reboots. Learning remains part of the project, but shipped behavior must work
as an operating system rather than as a presentation.

## Product contract

A useful first release should let a user:

1. Boot on a documented set of UEFI x86_64 machines and in a virtual machine.
2. Interact with a reliable terminal and launch multiple isolated user programs.
3. Recover from a faulty user program without losing the shell or the kernel.
4. Create and edit files and reopen them after a normal reboot.
5. Use a small set of coherent applications, including a shell and text editor.
6. Understand failures from actionable diagnostics rather than a silent hang.

Subsequent releases should expand input, graphics, networking, installation,
hardware coverage, and application support. These remain part of the long-term
goal; the first release is a milestone, not a replacement for that goal.

## Architectural direction

- Keep the kernel responsible for memory, scheduling, device access, process
  isolation, and the syscall boundary.
- Move ordinary interaction and applications into userspace. The current
  kernel shell remains useful during transition and recovery.
- Define a small documented syscall ABI before expanding applications.
- Keep the bootloader (Limine) until replacing it solves an actual user need.
- Treat a supported hardware list as a product contract. Broaden it only when
  boot, input, storage, and shutdown are verified on each target.
- Require end-to-end checks for core workflows; a ready marker alone proves
  only that initialization reached that point.

## Open decisions

- First physical hardware target and its storage/input/display devices.
- First persistent filesystem and the format or migration policy.
- Whether the initial interface remains terminal-first or ships a graphical
  desktop at the first release milestone.

## Evidence rule

No feature is called complete solely because source files or commands exist.
The feature inventory records observable acceptance steps and runtime evidence.
