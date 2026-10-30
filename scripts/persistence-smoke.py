#!/usr/bin/env python3
"""Save text in userspace, reboot, and read it from the same FAT16 image."""

import os
import select
import subprocess
import sys
import time


TIMEOUT_SECONDS = 90
FILE_PATH = "/PERSIST.TXT"


class Guest:
    def __init__(self):
        self.process = subprocess.Popen(
            ["qemu-system-x86_64", "-cdrom", "astraos.iso", "-boot", "order=d",
             "-drive", "file=disk.img,format=raw,if=ide", "-m", "256M",
             "-display", "none", "-monitor", "none", "-serial", "stdio",
             "-no-reboot"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0,
        )
        self.output = bytearray()
        self.cursor = 0

    def wait_for(self, marker):
        token = marker.encode("ascii")
        deadline = time.monotonic() + TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            position = self.output.find(token, self.cursor)
            if position >= 0:
                self.cursor = position + len(token)
                return
            if self.process.poll() is not None:
                raise RuntimeError(f"guest exited before {marker!r}")
            readable, _, _ = select.select([self.process.stdout], [], [], 0.5)
            if readable:
                self.output.extend(os.read(self.process.stdout.fileno(), 4096))
        raise TimeoutError(f"waiting for {marker!r}")

    def send(self, line):
        self.process.stdin.write(line.encode("ascii") + b"\r")
        self.process.stdin.flush()

    def login(self):
        self.wait_for("ASTRAOS_SMOKE_READY")
        self.wait_for("Username:")
        self.send("tester")
        self.wait_for("Password:")
        self.send("testpass")
        self.wait_for("$ ")

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


def main():
    guest = None
    try:
        guest = Guest()
        guest.login()
        guest.send("run /SH")
        guest.wait_for("user$ ")
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
        guest.send("run /SH")
        guest.wait_for("user$ ")
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
