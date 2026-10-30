#include "syscall.h"

int main(void) {
    static const char message[] = "FAULT_TEST_BEGIN\n";
    sys_write(1, message, sizeof(message) - 1);

    /* A user-mode invalid instruction must not bring down the kernel. */
    __asm__ volatile ("ud2");
    __builtin_unreachable();
}
