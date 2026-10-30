#!/usr/bin/env python3
"""Check that a busy user process cannot monopolize AstraOS."""

import os
import re
import select
import subprocess
import sys
import time


TIMEOUT_SECONDS = 180
REUSE_LAUNCHES = 70  # More than MAX_PROCESSES (64) if exited slots never return.


def main():
    guest = subprocess.Popen(
        [
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
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    output = bytearray()
    cursor = 0
    deadline = time.monotonic() + TIMEOUT_SECONDS

    def read_until(predicate, description):
        while time.monotonic() < deadline:
            result = predicate()
            if result is not None:
                return result
            if guest.poll() is not None:
                raise RuntimeError(f"QEMU exited with status {guest.returncode}")
            readable, _, _ = select.select([guest.stdout], [], [], 0.5)
            if readable:
                chunk = os.read(guest.stdout.fileno(), 4096)
                if chunk:
                    output.extend(chunk)
                elif guest.poll() is not None:
                    raise RuntimeError(f"QEMU exited with status {guest.returncode}")
        raise TimeoutError(f"Timed out waiting for {description}")

    def wait_for(marker):
        nonlocal cursor
        token = marker.encode("ascii")

        def found():
            nonlocal cursor
            position = output.find(token, cursor)
            if position < 0:
                return None
            cursor = position + len(token)
            return position

        return read_until(found, repr(marker))

    def wait_for_regex(pattern):
        nonlocal cursor
        expression = re.compile(pattern)

        def found():
            nonlocal cursor
            match = expression.search(output, cursor)
            if match is None:
                return None
            cursor = match.end()
            return match

        return read_until(found, repr(pattern))

    def wait_for_both(first, second):
        nonlocal cursor
        start = cursor
        a = first.encode("ascii")
        b = second.encode("ascii")

        def found():
            nonlocal cursor
            a_pos = output.find(a, start)
            b_pos = output.find(b, start)
            if a_pos < 0 or b_pos < 0:
                return None
            cursor = max(a_pos + len(a), b_pos + len(b))
            return True

        return read_until(found, repr((first, second)))

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

        send("run /SPIN &")
        match = wait_for_regex(rb"Started user process /SPIN as PID ([0-9]+)\r?\n")
        first_pid = int(match.group(1))
        wait_for_both("$ ", "SPIN_READY")

        # The second busy process must also run while the first stays runnable.
        send("run /SPIN &")
        match = wait_for_regex(rb"Started user process /SPIN as PID ([0-9]+)\r?\n")
        second_pid = int(match.group(1))
        if first_pid == second_pid:
            raise RuntimeError("two live busy processes received the same PID")
        wait_for_both("$ ", "SPIN_READY")

        # A kernel-shell command must complete while both processes are running.
        send("uptime")
        wait_for("Uptime:")
        wait_for("$ ")

        for pid in (first_pid, second_pid):
            send(f"kill {pid}")
            wait_for(f"Killed process {pid}")
            wait_for("$ ")

        # Launch enough children to exceed the fixed process table if slots leak.
        for _ in range(REUSE_LAUNCHES):
            send("run /HELLO")
            wait_for("hello from AstraOS ring 3")
            wait_for("exited with status 0")
            wait_for("$ ")

        print(f"Both SPIN processes ran; shell handled uptime and killed PIDs {first_pid}, {second_pid}")
        print(f"Preemption smoke passed: {REUSE_LAUNCHES} healthy launches reused process slots")
        return 0
    except (OSError, RuntimeError, TimeoutError) as error:
        print(f"Preemption smoke failed: {error}", file=sys.stderr)
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
