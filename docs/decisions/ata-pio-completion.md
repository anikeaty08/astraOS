# ATA PIO command completion

Decision recorded 2026-10-30. The current FAT16 test disk uses the kernel's ATA PIO driver.

## Observed failure

An editor integration run reported save failure after a rename, while host inspection found both the new target file and the old backup on disk. Earlier failed temporary-file creation attempts also left zero-length directory entries. The driver used a fixed 100,000-iteration status poll and considered `RDY` sufficient even while `DRQ` remained set. The result could be an error after a write had already changed media. This observation does not by itself prove which specific status bit or timing condition caused each failure.

## Choice

Poll for at most two seconds using the PIT that is initialized before ATA. Keep a large iteration cap as a fallback if ticks do not advance. Before issuing a new command, require `BSY=0`, `DRQ=0`, and `RDY=1`; for a PIO data transfer, require `BSY=0` and `DRQ=1`. Treat `ERR` and device fault as failures after `BSY` clears. The [T13 ATA/ATAPI draft](https://pdos.csail.mit.edu/6.828/2010/readings/hardware/ATA-d1410r3a.pdf) describes the command/status sequencing, including the need for `BSY` and `DRQ` to clear before writing a command register. [QEMU's IDE implementation](https://github.com/qemu/qemu/blob/master/hw/ide/core.c) shows its emulated status and PIO state transitions. **Inference:** a time-based deadline and complete status condition should reduce false failures under emulation load.

## Verification and remaining risk

Three consecutive local editor save/reboot runs passed after the change. CI and real-hardware behavior still require separate evidence. Even with correct polling, a failed write can have taken effect before the error is returned; higher layers must inspect postconditions and retain recovery copies. This does not establish power-loss durability.
