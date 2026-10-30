# AstraOS Makefile
# x86_64 Hobby Operating System

# Toolchain - uses Linux gcc in freestanding mode
# On Linux/WSL: uses system gcc
# For true cross-compile: install x86_64-elf-gcc and change CC/LD
CC := gcc
AS := nasm
LD := ld

# Compiler flags - CRITICAL for kernel development
CFLAGS := -ffreestanding \
          -fno-stack-protector \
          -fno-stack-check \
          -fno-pie \
          -fno-pic \
          -mno-red-zone \
          -mno-80387 \
          -mno-mmx \
          -mno-sse \
          -mno-sse2 \
          -mcmodel=kernel \
          -Wall \
          -Wextra \
          -Werror \
          -std=gnu11 \
          -O2 \
          -g \
          -Ikernel

ASFLAGS := -f elf64 -g

LDFLAGS := -nostdlib \
           -static \
           -z max-page-size=0x1000 \
           -T linker.ld

# Source files
C_SOURCES := $(shell find kernel -name '*.c')
ASM_SOURCES := $(shell find kernel -name '*.asm')

# Object files
C_OBJECTS := $(C_SOURCES:.c=.o)
ASM_OBJECTS := $(ASM_SOURCES:.asm=.o)
OBJECTS := $(C_OBJECTS) $(ASM_OBJECTS)

# Output files
KERNEL := iso/kernel.elf
ISO := astraos.iso
DISK := disk.img
USER_BUILD := build/user
USER_PROGRAMS := sh hello pkg fault spin
USER_BINS := $(addprefix $(USER_BUILD)/,$(USER_PROGRAMS))
USER_CFLAGS := -ffreestanding -fno-stack-protector -fno-pie -fno-pic \
               -mno-red-zone -mno-80387 -mno-mmx -mno-sse -mno-sse2 \
               -nostdlib -static -O2 -Wall -Wextra -Werror \
               -std=gnu11 -Iuserspace -T userspace/linker.ld

# Limine bootloader path (adjust after cloning)
LIMINE_DIR := limine

.PHONY: all clean run run-debug run-gdb iso limine disk userspace smoke fault-smoke preemption-smoke persistence-smoke

all: $(KERNEL) userspace

$(KERNEL): $(OBJECTS)
	@mkdir -p iso
	$(LD) $(LDFLAGS) -o $@ $^
	@echo "Kernel built: $@"

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.asm
	$(AS) $(ASFLAGS) $< -o $@

$(USER_BUILD):
	@mkdir -p $(USER_BUILD)

$(USER_BUILD)/crt0.o: userspace/crt0.asm | $(USER_BUILD)
	$(AS) $(ASFLAGS) $< -o $@

$(USER_BUILD)/sh: userspace/sh.c userspace/shell/file_commands.c userspace/shell/file_commands.h $(USER_BUILD)/crt0.o userspace/linker.ld userspace/syscall.h | $(USER_BUILD)
	$(CC) $(USER_CFLAGS) $(USER_BUILD)/crt0.o userspace/sh.c userspace/shell/file_commands.c -o $@

$(USER_BUILD)/%: userspace/%.c $(USER_BUILD)/crt0.o userspace/linker.ld userspace/syscall.h | $(USER_BUILD)
	$(CC) $(USER_CFLAGS) $(USER_BUILD)/crt0.o $< -o $@

userspace: $(USER_BINS)

# Clone Limine if not present
limine:
	@if [ ! -f "$(LIMINE_DIR)/limine.c" ]; then \
		if [ -d "$(LIMINE_DIR)" ] && [ -n "$$(ls -A "$(LIMINE_DIR)")" ]; then \
			echo "Incomplete Limine checkout in $(LIMINE_DIR)" >&2; \
			exit 1; \
		fi; \
		echo "Cloning Limine bootloader..."; \
		git clone https://github.com/limine-bootloader/limine.git --branch=v8.x-binary --depth=1 "$(LIMINE_DIR)"; \
	fi
	$(MAKE) -C "$(LIMINE_DIR)" limine

# Build ISO image
iso: $(KERNEL) limine
	@echo "Building ISO..."
	cp limine.conf iso/
	cp $(LIMINE_DIR)/limine-bios.sys iso/
	cp $(LIMINE_DIR)/limine-bios-cd.bin iso/
	cp $(LIMINE_DIR)/limine-uefi-cd.bin iso/
	mkdir -p iso/EFI/BOOT
	cp $(LIMINE_DIR)/BOOTX64.EFI iso/EFI/BOOT/
	cp $(LIMINE_DIR)/BOOTIA32.EFI iso/EFI/BOOT/
	xorriso -as mkisofs -b limine-bios-cd.bin \
		-no-emul-boot -boot-load-size 4 -boot-info-table \
		--efi-boot limine-uefi-cd.bin \
		-efi-boot-part --efi-boot-image --protective-msdos-label \
		iso -o $(ISO)
	$(LIMINE_DIR)/limine bios-install $(ISO)
	@echo "ISO built: $(ISO)"

disk: userspace
	rm -f $(DISK)
	dd if=/dev/zero of=$(DISK) bs=1M count=32
	mkfs.fat -F 16 $(DISK)
	mcopy -i $(DISK) $(USER_BUILD)/sh ::/SH
	mcopy -i $(DISK) $(USER_BUILD)/hello ::/HELLO
	mcopy -i $(DISK) $(USER_BUILD)/pkg ::/PKG
	mcopy -i $(DISK) $(USER_BUILD)/fault ::/FAULT
	mcopy -i $(DISK) $(USER_BUILD)/spin ::/SPIN

# Run in QEMU
run: iso disk
	qemu-system-x86_64 \
		-cdrom $(ISO) \
		-boot order=d \
		-drive file=$(DISK),format=raw,if=ide \
		-m 256M \
		-serial stdio \
		-no-reboot \
		-no-shutdown

# Run with interrupt debugging
run-debug: iso disk
	qemu-system-x86_64 \
		-cdrom $(ISO) \
		-boot order=d \
		-drive file=$(DISK),format=raw,if=ide \
		-m 256M \
		-serial stdio \
		-d int,cpu_reset \
		-no-reboot \
		-no-shutdown

# Run with GDB support
run-gdb: iso disk
	qemu-system-x86_64 \
		-cdrom $(ISO) \
		-boot order=d \
		-drive file=$(DISK),format=raw,if=ide \
		-m 256M \
		-serial stdio \
		-s -S \
		-no-reboot \
		-no-shutdown &
	@echo "QEMU started. Connect with: gdb iso/kernel.elf -ex 'target remote :1234'"

smoke:
	sh ./scripts/smoke.sh

fault-smoke: iso disk
	python3 ./scripts/fault-smoke.py

preemption-smoke: iso disk
	python3 ./scripts/preemption-smoke.py

persistence-smoke: iso disk
	python3 ./scripts/persistence-smoke.py

# Clean build artifacts
clean:
	rm -f $(OBJECTS) $(KERNEL) $(ISO) $(DISK)
	rm -rf iso/*.sys iso/*.bin iso/*.conf iso/*.elf iso/EFI
	rm -rf smoke-logs
	rm -rf build

# Deep clean (including Limine)
distclean: clean
	rm -rf $(LIMINE_DIR)

# Show help
help:
	@echo "AstraOS Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all        - Build kernel"
	@echo "  iso        - Build bootable ISO"
	@echo "  userspace  - Build user-space ELF binaries"
	@echo "  disk       - Build FAT16 user program disk image"
	@echo "  run        - Run in QEMU"
	@echo "  run-debug  - Run with interrupt debugging"
	@echo "  run-gdb    - Run with GDB support"
	@echo "  smoke      - Build and run headless QEMU smoke test"
	@echo "  fault-smoke - Verify user faults leave the shell and other apps usable"
	@echo "  preemption-smoke - Verify busy apps can be killed and process slots reused"
	@echo "  persistence-smoke - Verify userspace saves survive a guest reboot"
	@echo "  clean      - Remove build artifacts"
	@echo "  distclean  - Remove everything including Limine"
	@echo "  help       - Show this help"
