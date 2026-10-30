#!/usr/bin/env python3
"""Save text in userspace, reboot, and read it from the same FAT16 image."""

import subprocess
import sys

from qemu_guest import Guest


FILE_PATH = "/PERSIST.TXT"


def main():
    guest = None
    try:
        guest = Guest()
        guest.login()
        guest.send(f"write {FILE_PATH} first version")
        guest.wait_for("saved")
        guest.wait_for("user$ ")
        guest.send(f"write {FILE_PATH} final version")
        guest.wait_for("saved")
        guest.wait_for("user$ ")
        guest.send(f"cat {FILE_PATH}")
        guest.wait_for("final version")
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
        guest.send(f"cat {FILE_PATH}")
        guest.wait_for("final version")
        guest.wait_for("user$ ")
        saved = subprocess.check_output(["mtype", "-i", "disk.img", "::/PERSIST.TXT"])
        if saved != b"final version\n":
            raise RuntimeError(f"unexpected on-disk bytes: {saved!r}")
        print("Persistence smoke passed: userspace replacement survived guest reboot")
        return 0
    except (OSError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as error:
        print(f"Persistence smoke failed: {error}", file=sys.stderr)
        if guest is not None:
            print(guest.output[-12000:].decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    finally:
        if guest is not None:
            guest.close()


if __name__ == "__main__":
    raise SystemExit(main())
