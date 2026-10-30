# Feature contract: persistent text workflow

## Goal

From a userspace application, create a text file, replace its contents, inspect it, reboot normally with the **same disk image**, and read the exact contents. This is the first complete user-data workflow. FAT16 remains the implementation under the VFS.

## Initial interface

Add `write <path> <text>` to the existing userspace shell as a small first step. It writes one line plus a newline to a root-level FAT16 8.3 filename. `cat <path>` already reads through the syscall/VFS path. A full-screen editor and shell argument passing belong to the following userspace-session slice; this command exercises the same storage boundary immediately without inventing a separate kernel-only path.

The command should reject empty paths/text and a path it cannot create or open for writing. `sys_create` creates **only a new file** in the current VFS. For an existing file, add an explicit writable-open mode to the syscall and descriptor contract, then truncate it to zero before writing. A descriptor opened read-only must reject writes. Write loops must handle partial results. An error must be printed; do not claim a save succeeded after any failed call. Close the descriptor on every path.

## Data flow and invariants

Input line → userspace parser → bounded path and text → `SYS_CREATE` (new) or writable `SYS_OPEN` (existing) → `SYS_TRUNCATE` (existing) → `SYS_WRITE` until complete → `SYS_CLOSE` → optional `cat` readback → QEMU exit → second QEMU boot with the same disk image → `cat` and byte comparison. The test must not run `make disk` between boots because that would recreate the image. The first step proves normal-reboot persistence only.

The test uses a unique root-level 8.3 filename, checks both the initial and replaced content, and verifies the second boot. It must detect obvious save errors. Invalid names and short writes are separate focused cases. The current FAT16 write path has no documented atomic replacement or flush guarantee; power interruption may damage data and is outside this first gate.

## Follow-up after acceptance

Extract the line editor as a standalone ELF app once argument passing and terminal ownership are defined. Add multi-line editing, append/insert/delete, explicit save and discard, and file-size limits. Introduce a writable-open mode rather than relying indefinitely on create/truncate. Add `fsync`/block flush and fault injection before promising crash-safe saves.
