#!/usr/bin/env python3
"""Verify default userspace shell, restart limit, and kernel recovery fallback."""

import subprocess
import sys
import shutil
import pathlib
import tempfile

from qemu_guest import Guest


def main():
    guest = None
    try:
        guest = Guest()
        guest.login()
        guest.send("exit " + "9" * 100)
        guest.wait_for("expected a code from 0 to 255")
        guest.wait_for("user$ ")
        guest.send("run /HELLO")
        guest.wait_for("hello from AstraOS ring 3")
        guest.wait_for("process exited 0")
        guest.wait_for("user$ ")
        guest.send("run /ARGS a b c d e f g")
        guest.wait_for("argc=8")
        guest.wait_for("arg0=/ARGS")
        guest.wait_for("arg7=g")
        guest.wait_for("process exited 0")
        guest.wait_for("user$ ")

        guest.send("run /EDIT /ARGS.TXT")
        guest.wait_for("new file")
        guest.wait_for("edit> ")
        guest.send("q!")
        guest.wait_for("process exited 0")
        guest.wait_for("user$ ")
        guest.send("run /EDIT a b c d e f g h")
        guest.wait_for("run: at most 8 arguments")
        guest.wait_for("user$ ")

        for attempt in range(1, 4):
            guest.send("exit 1")
            guest.wait_for("exited with status 1")
            if attempt < 3:
                guest.wait_for(f"restarting ({attempt}/3)")
                guest.wait_for("user$ ")
            else:
                guest.wait_for("failed three times; entering kernel recovery shell")
                guest.wait_for("$ ")

        guest.send("run /SH")
        guest.wait_for("user$ ")
        guest.send("exit")
        guest.wait_for("exited with status 0")
        guest.wait_for("$ ")
        guest.close()
        guest = None

        with tempfile.TemporaryDirectory() as directory:
            missing_shell_disk = pathlib.Path(directory) / "missing-shell.img"
            shutil.copyfile("disk.img", missing_shell_disk)
            subprocess.run(["mdel", "-i", str(missing_shell_disk), "::/SH"], check=True)
            guest = Guest(disk_image=str(missing_shell_disk))
            guest.wait_for("ASTRAOS_SMOKE_READY")
            guest.wait_for("Username:")
            guest.send("tester")
            guest.wait_for("Password:")
            guest.send("testpass")
            guest.wait_for("User shell unavailable; entering kernel recovery shell")
            guest.wait_for("$ ")
            guest.send("uptime")
            guest.wait_for("$ ")
            guest.close()
            guest = None
        subprocess.run(["mdir", "-i", "disk.img", "::/SH"], check=True,
                       stdout=subprocess.DEVNULL)
        print("Session smoke passed: default shell, bounded restart, and recovery fallback")
        return 0
    except (OSError, RuntimeError, TimeoutError, subprocess.CalledProcessError) as error:
        print(f"Session smoke failed: {error}", file=sys.stderr)
        if guest is not None:
            print(guest.output[-12000:].decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    finally:
        if guest is not None:
            guest.close()


if __name__ == "__main__":
    raise SystemExit(main())
