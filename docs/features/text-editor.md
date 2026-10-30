# Feature contract: standalone text editor

## User workflow

From the kernel shell, `run /EDIT` starts a userspace editor. From the userspace shell, `run /EDIT` starts it in the foreground; the shell waits and resumes when it exits. The editor asks for a root-level FAT16 path, loads existing text or starts an empty file, lets the user list, append, insert, and delete lines, and saves on an explicit `w` command. `q` exits only when unchanged; `q!` discards changes.

This is a line editor, deliberately usable over serial and framebuffer text before a terminal/surface ABI exists. It is an independent ELF program, not a command embedded in the kernel. A graphical editor can later reuse file and session contracts. The initial implementation and QEMU test are complete; durability and concurrency limits below remain.

## Limits and commands

- File path: absolute root-level FAT16 8.3 name, up to 12 printable characters after `/`; reject invalid or overlong names before any write.
- File: at most 32 lines of up to 95 bytes each. Existing larger or binary files are rejected without modification. A line is separated by `\n`; optional `\r` before it is ignored.
- Commands: `p` print numbered lines, `a <text>` append, `i <n> <text>` insert before 1-based line `n`, `d <n>` delete, `w` save, `q` exit if clean, `q!` discard, `h` help. Empty lines can be appended with `a`.
- Save reports success only after every write and close succeeds. A failed save keeps the editor open and marked dirty. The current FAT16 path is not power-loss safe; `w` currently replaces by truncating an existing file.

## Boundaries and validation

The editor owns its bounded in-memory text model. It accesses files only through `sys_open`, `sys_create`, `sys_open_write`, `sys_truncate`, `sys_read`, `sys_write`, and `sys_close`. The userspace shell owns child launch/wait and therefore console focus for a foreground program. The kernel owns pointer validation, permissions, and per-process descriptor access. Path validation in the editor improves UX but the kernel remains the security boundary.

An overlong input command is drained to its newline and rejected as a whole. The editor must never silently truncate an existing file while loading it. It does not support concurrent edits; after boot, opening the same file in two editors can overwrite another editor's save. A later VFS generation/version or locking contract is needed for that case.

## Acceptance

1. Launch `/EDIT` from `/SH`; create a note with at least two lines, insert and delete a line, print it, save, and return to the shell.
2. Reopen the note in `/EDIT`, change a line, save, reboot the guest with the same disk image, and compare exact bytes from the host.
3. Verify `q` refuses dirty changes and `q!` discards them; invalid paths and oversized inputs leave existing data unchanged.
4. Existing boot, fault, preemption, and persistence checks continue to pass.
