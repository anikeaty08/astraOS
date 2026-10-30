#!/usr/bin/env python3
"""Exercise standalone editor, foreground console ownership, and reboot save."""

import subprocess
import sys

from qemu_guest import Guest


PATH = "/NOTES.TXT"


def command(guest, line, expected=None):
    guest.send(line)
    if expected is not None:
        guest.wait_for(expected)
    guest.wait_for("edit> ")


def main():
    guest = None
    try:
        guest = Guest()
        guest.login()
        guest.send("run /EDIT")
        guest.wait_for("path: ")
        guest.send("/TOO-LONG-NAME.TXT")
        guest.wait_for("use a root-level 8.3 path")
        guest.wait_for("process exited 1")
        guest.wait_for("user$ ")

        guest.send("run /EDIT")
        guest.wait_for("path: ")
        guest.send(PATH)
        guest.wait_for("new file")
        guest.wait_for("edit> ")

        command(guest, "a alpha")
        command(guest, "a gamma")
        command(guest, "i 2 beta")
        command(guest, "d 3")
        command(guest, "p", "2: beta")
        command(guest, "q", "unsaved changes")
        command(guest, "w", "saved")
        guest.send("q")
        guest.wait_for("process exited 0")
        guest.wait_for("user$ ")

        guest.send("run /EDIT")
        guest.wait_for("path: ")
        guest.send(PATH)
        guest.wait_for("loaded 2 lines")
        guest.wait_for("edit> ")
        command(guest, "a " + "x" * 180, "command too long")
        command(guest, "p", "2: beta")
        command(guest, "a discarded")
        guest.send("q!")
        guest.wait_for("process exited 0")
        guest.wait_for("user$ ")

        guest.send("run /EDIT")
        guest.wait_for("path: ")
        guest.send(PATH)
        guest.wait_for("loaded 2 lines")
        guest.wait_for("edit> ")
        command(guest, "d 1")
        command(guest, "i 1 revised")
        command(guest, "w", "saved")
        guest.send("q")
        guest.wait_for("process exited 0")
        guest.wait_for("user$ ")
        guest.send("exit")
        guest.wait_for("exited with status 0")
        guest.wait_for("$ ")
        guest.send("reboot")
        guest.wait_for("Rebooting...")
        guest.process.wait(timeout=15)
        guest.close()

        guest = Guest()
        guest.login()
        guest.send(f"cat {PATH}")
        guest.wait_for("revised\nbeta")
        guest.wait_for("user$ ")
        saved = subprocess.check_output(["mtype", "-i", "disk.img", "::/NOTES.TXT"])
        if saved != b"revised\nbeta\n":
            raise RuntimeError(f"unexpected on-disk bytes: {saved!r}")
        print("Editor smoke passed: multi-line edits and discard worked; save survived reboot")
        return 0
    except (OSError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as error:
        print(f"Editor smoke failed: {error}", file=sys.stderr)
        if guest is not None:
            print(guest.output[-12000:].decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    finally:
        if guest is not None:
            guest.close()


if __name__ == "__main__":
    raise SystemExit(main())
