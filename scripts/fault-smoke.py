#!/usr/bin/env python3
"""Exercise user fault recovery through the real serial console."""

import os
import select
import subprocess
import sys
import time


TIMEOUT_SECONDS = 60


def main():
    command = [
        "qemu-system-x86_64",
        "-cdrom", "astraos.iso",
        "-boot", "order=d",
        "-drive", "file=disk.img,format=raw,if=ide",
        "-m", "256M",
        "-display", "none",
        "-monitor", "none",
        "-serial", "stdio",
        "-no-reboot",
        "-no-shutdown",
    ]
    guest = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    output = bytearray()
    cursor = 0
    deadline = time.monotonic() + TIMEOUT_SECONDS

    def wait_for(marker):
        nonlocal cursor
        token = marker.encode("ascii")
        while time.monotonic() < deadline:
            position = output.find(token, cursor)
            if position >= 0:
                cursor = position + len(token)
                return
            if guest.poll() is not None:
                raise RuntimeError(f"QEMU exited with status {guest.returncode}")
            readable, _, _ = select.select([guest.stdout], [], [], 0.5)
            if readable:
                chunk = os.read(guest.stdout.fileno(), 4096)
                if chunk:
                    output.extend(chunk)
                elif guest.poll() is not None:
                    raise RuntimeError(f"QEMU exited with status {guest.returncode}")
        raise TimeoutError(f"Timed out waiting for {marker!r}")

    def send(line):
        guest.stdin.write(line.encode("ascii") + b"\r")
        guest.stdin.flush()

    try:
        wait_for("ASTRAOS_SMOKE_READY")
        wait_for("Username:")
        send("tester")
        wait_for("Password:")
        send("testpass")
        wait_for("user$ ")
        send("exit")
        wait_for("$ ")
        send("run /FAULT")
        wait_for("FAULT_TEST_BEGIN")
        wait_for("USER PROCESS FAULT pid=")
        wait_for("vector=6")
        wait_for("exited with status -7")
        wait_for("$ ")
        send("run /HELLO")
        wait_for("hello from AstraOS ring 3")
        wait_for("exited with status 0")
        for line in output.decode("utf-8", errors="replace").splitlines():
            if ("FAULT_TEST_BEGIN" in line or "USER PROCESS FAULT" in line or
                    "exited with status" in line or
                    "hello from AstraOS ring 3" in line):
                print(line.strip())
        print("Fault smoke passed: user fault was isolated and /HELLO still ran")
        return 0
    except (OSError, RuntimeError, TimeoutError) as error:
        print(f"Fault smoke failed: {error}", file=sys.stderr)
        print(output[-12000:].decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    finally:
        guest.terminate()
        try:
            guest.wait(timeout=5)
        except subprocess.TimeoutExpired:
            guest.kill()
            guest.wait()


if __name__ == "__main__":
    raise SystemExit(main())
