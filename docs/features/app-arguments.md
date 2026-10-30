# Feature contract: native app arguments

## User workflow

The userspace shell accepts `run /PROGRAM [arguments]`. For example,
`run /EDIT /NOTE.TXT` opens that file directly. `run /EDIT` still prompts for a
path. Arguments are separated by spaces or tabs; quoting and environment
variables are not yet implemented.

## ABI and ownership

- `SYS_SPAWNV` takes an executable path, an argument count, and a user pointer
  to an array of argument pointers. `SYS_SPAWN` remains available for old apps.
- The syscall boundary copies every pointer and string before loading the ELF.
  It rejects unmapped pointers, more than eight arguments, or more than 512
  bytes of strings including terminators. A failed validation creates no child.
- The process loader owns the initial user stack. It places `argc`, `argv[]`, a
  null terminator, an empty environment, and a null auxiliary entry on a
  16-byte-aligned stack. The freestanding runtime passes `argc` and `argv` to
  `main`. This follows the initial process stack shape in the
  [AMD64 System V ABI](https://cs61.seas.harvard.edu/site/2024/pdf/x86-64-abi-20210928.pdf).
- The kernel shell and legacy `SYS_SPAWN` supply the executable path as
  `argv[0]`. The user shell supplies its parsed first token as `argv[0]`.

## Verification and limits

`make session-smoke` checks that `/EDIT` receives a path and returns control
to the shell. The `/ARGS` utility reports the eight-element vector, and an
overlong argument list is rejected by the shell.
`make editor-smoke` checks that the interactive path fallback still works.
The current stack has an empty environment and no useful auxiliary entries;
dynamic ELF linking, quoting, globbing, and third-party ABI compatibility are
separate work.
