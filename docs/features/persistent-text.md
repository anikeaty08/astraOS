# Feature contract: persistent text workflow

## Goal

From a userspace application, create a text file, replace its contents, inspect it, reboot normally with the **same disk image**, and read the exact contents. This is the first complete user-data workflow. FAT16 remains the implementation under the VFS.

## Initial interface

Add `write <path> <text>` to the existing userspace shell as a small first step. It writes one line plus a newline to a root-level FAT16 8.3 filename. `cat <path>` already reads through the syscall/VFS path. A full-screen editor and shell argument passing belong to the following userspace-session slice; this command exercises the same storage boundary immediately without inventing a separate kernel-only path.

The command rejects empty paths/text and paths outside the supported root-level 8.3 subset. `sys_create` creates **only a new file** in the current VFS. A descriptor opened read-only rejects writes. The current shell and editor share a userspace replacement routine: write the complete new data to a unique temporary file, close it, rename an existing original to a backup, then promote the temporary file. A failed promotion attempts to restore the backup and reports its path if restoration fails. Write loops handle partial results and a failed call cannot be reported as success.

## Data flow and invariants

Input line → userspace parser → bounded path and text → unique temporary `SYS_CREATE` → `SYS_WRITE` until complete → `SYS_CLOSE` → old-name backup and temporary-name promotion through `SYS_RENAME` → optional `cat` readback → QEMU exit → second QEMU boot with the same disk image → `cat` and byte comparison. The test must not run `make disk` between boots because that would recreate the image. The first step proves normal-reboot persistence only. The temporary/backup sequence is a best-effort rollback for ordinary write errors, not an atomic disk transaction.

The test uses a root-level 8.3 filename, checks save responses, checks the replaced content after the second boot, and compares the exact on-disk bytes from the host. Invalid names and short writes are separate focused cases. The current FAT16 write path has no documented atomic replacement or flush guarantee; power interruption may damage data and is outside this first gate.

## Follow-up after acceptance

The standalone line editor now exists with multi-line editing, append/insert/delete, explicit save and discard, and file-size limits. Add `fsync`/block flush and fault injection before promising crash-safe saves. The VFS still needs coherent nodes or fd-based truncate for other callers that modify an open file through a separate path lookup.
