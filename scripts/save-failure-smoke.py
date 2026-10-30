#!/usr/bin/env python3
"""Fill the FAT16 image and verify a failed replacement preserves old data."""

import pathlib
import re
import subprocess
import sys
import tempfile

from qemu_guest import Guest


PATH = "/NOTE.TXT"
ORIGINAL = b"original\n"


def free_bytes():
    listing = subprocess.check_output(["mdir", "-i", "disk.img", "::/"], text=True)
    match = re.search(r"([0-9 ]+) bytes free", listing)
    if not match:
        raise RuntimeError("cannot read FAT16 free-space count")
    return int(match.group(1).replace(" ", ""))


def prepare_full_disk():
    with tempfile.TemporaryDirectory() as directory:
        original = pathlib.Path(directory) / "original.txt"
        original.write_bytes(ORIGINAL)
        subprocess.run(["mcopy", "-i", "disk.img", str(original), "::/NOTE.TXT"], check=True)

        filler = pathlib.Path(directory) / "filler.bin"
        with filler.open("wb") as file:
            file.truncate(free_bytes())
        subprocess.run(["mcopy", "-i", "disk.img", str(filler), "::/FILL.BIN"], check=True)
    if free_bytes() != 0:
        raise RuntimeError("test disk still has free clusters")


def assert_original():
    data = subprocess.check_output(["mtype", "-i", "disk.img", "::/NOTE.TXT"])
    if data != ORIGINAL:
        raise RuntimeError(f"old file changed after failed save: {data!r}")


def main():
    guest = None
    try:
        prepare_full_disk()
        guest = Guest()
        guest.login()
        guest.send(f"write {PATH} replacement")
        guest.wait_for("write: save failed")
        guest.wait_for("user$ ")
        assert_original()

        guest.send("run /EDIT")
        guest.wait_for("path: ")
        guest.send(PATH)
        guest.wait_for("loaded 1 lines")
        guest.wait_for("edit> ")
        guest.send("a more")
        guest.wait_for("edit> ")
        guest.send("w")
        guest.wait_for("edit: save failed")
        guest.wait_for("edit> ")
        guest.send("q")
        guest.wait_for("unsaved changes")
        guest.wait_for("edit> ")
        guest.send("q!")
        guest.wait_for("process exited 0")
        assert_original()
        print("Save-failure smoke passed: full disk left original file intact")
        return 0
    except (OSError, RuntimeError, TimeoutError, subprocess.CalledProcessError) as error:
        print(f"Save-failure smoke failed: {error}", file=sys.stderr)
        if guest is not None:
            print(guest.output[-12000:].decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    finally:
        if guest is not None:
            guest.close()


if __name__ == "__main__":
    raise SystemExit(main())
