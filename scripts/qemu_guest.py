"""Minimal serial-console driver shared by interactive QEMU checks."""

import os
import select
import subprocess
import time


class Guest:
    def __init__(self, timeout_seconds=90, disk_image="disk.img"):
        self.process = subprocess.Popen(
            ["qemu-system-x86_64", "-cdrom", "astraos.iso", "-boot", "order=d",
             "-drive", f"file={disk_image},format=raw,if=ide", "-m", "256M",
             "-display", "none", "-monitor", "none", "-serial", "stdio",
             "-no-reboot"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0,
        )
        self.timeout_seconds = timeout_seconds
        self.output = bytearray()
        self.cursor = 0

    def wait_for(self, marker):
        token = marker.encode("ascii")
        deadline = time.monotonic() + self.timeout_seconds
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
        self.wait_for("user$ ")

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
