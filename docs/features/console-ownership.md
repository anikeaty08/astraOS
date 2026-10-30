# Feature contract: console input ownership

## User behavior

The normal shell owns console input after login. A foreground launch gives
input to the child; when that child exits or is killed, input returns to its
live parent. A background launch never gains input. A background app's
`read(0)` returns `-1` before it can take a character from the shell.

## Boundary and lifecycle

- The process subsystem stores one foreground process, initially the kernel
  shell. Only its child may acquire the console from it.
- The kernel shell transfers ownership for foreground launches and detaches
  background children. A native app launch transfers ownership only if its
  parent currently owns it.
- The syscall boundary checks ownership for console descriptor 0 before
  calling the keyboard reader. File descriptors 3 and above are unaffected.
- Exit, fault, and kill restore ownership to a live parent or the kernel
  recovery shell. Detaching a foreground child is refused.

This follows the one-foreground-reader principle described for controlling
terminals in the [Linux process-group manual](https://man7.org/linux/man-pages/man2/getpgrp.2.html).
AstraOS currently tracks one process, not a POSIX process group. It returns
an error for background reads because stop and resume signals do not exist.

## Verification and limits

`make session-smoke` runs `/INPUT` in the foreground and checks that it reads
a line. It then launches `/INPUT` in the background from the recovery shell,
checks `INPUT_DENIED`, and confirms the shell still accepts a command. Existing
editor and fault checks cover return to the parent after app exit and fault.

The keyboard reader can still wait inside the kernel. There is no terminal
interrupt key, signal delivery, process group, job control, or PTY. Those are
needed before an active foreground app can be interrupted from the keyboard.
